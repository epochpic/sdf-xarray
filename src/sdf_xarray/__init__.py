import os
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from itertools import product
from pathlib import Path
from typing import ClassVar

import numpy as np
import xarray as xr
from xarray.backends import AbstractDataStore, BackendArray, BackendEntrypoint
from xarray.backends.file_manager import CachingFileManager
from xarray.backends.locks import ensure_lock
from xarray.core import indexing
from xarray.core.utils import close_on_error, try_read_magic_number_from_path
from xarray.core.variable import Variable

# NOTE: Do not delete this line, otherwise the "epoch" accessor will not be
# imported when the user imports sdf_xarray
import sdf_xarray.plotting  # noqa: F401

from .sdf_interface import Constant, SDFFile  # type: ignore  # noqa: PGH003


def _rename_with_underscore(name: str) -> str:
    """A lot of the variable names have spaces, forward slashes and dashes in them, which
    are not valid in netCDF names so we replace them with underscores."""
    return name.replace("/", "_").replace(" ", "_").replace("-", "_")


def _process_latex_name(variable_name: str) -> str:
    """Converts variable names to LaTeX format where possible
    using the following rules:
    - E -> $E_x$
    - E -> $E_y$
    - E -> $E_z$

    This repeats for B, J and P. It only changes the variable
    name if there are spaces around the affix (prefix + suffix)
    or if there is no trailing space. This is to avoid changing variable
    names that may contain these affixes as part of the variable name itself.
    """
    prefixes = ["E", "B", "J", "P"]
    suffixes = ["x", "y", "z"]
    for prefix, suffix in product(prefixes, suffixes):
        # Match affix with preceding space and trailing space or end of string
        affix_pattern = rf"\b{prefix}{suffix}\b"
        # Insert LaTeX format while preserving spaces
        replacement = rf"${prefix}_{suffix}$"
        variable_name = re.sub(affix_pattern, replacement, variable_name)
    return variable_name


def combine_datasets(path_glob: Iterable | str, **kwargs) -> xr.Dataset:
    """Combine all datasets using a single time dimension"""

    return xr.open_mfdataset(
        path_glob,
        data_vars="minimal",
        coords="minimal",
        compat="override",
        preprocess=SDFPreprocess(),
        **kwargs,
    )


def open_mfdataset(
    path_glob: Iterable | str | Path | Callable[..., Iterable[Path]],
    *,
    separate_times: bool = False,
    keep_particles: bool = False,
) -> xr.Dataset:
    """Open a set of EPOCH SDF files as one `xarray.Dataset`

    EPOCH can output variables at different periods, so each individal
    SDF file from one EPOCH run may have different variables in it. In
    order to combine all files into one `xarray.Dataset`, we need to
    concatenate variables across their time dimension.

    We have two choices:

    1. One time dimension where some variables may not be defined at all time
       points, and so will be filled with NaNs at missing points; or
    2. Multiple time dimensions, one for each output frequency

    The second option is better for memory consumption, as the missing data with
    the first option still takes up space. However, proper lazy-loading may
    mitigate this.

    The ``separate_times`` argument can be used to switch between these choices.

    Parameters
    ----------
    path_glob :
        List of filenames or string glob pattern
    separate_times :
        If ``True``, create separate time dimensions for variables defined at
        different output frequencies
    keep_particles :
        If ``True``, also load particle data (this may use a lot of memory!)
    """

    # TODO: This is not very robust, look at how xarray.open_mfdataset does it
    if isinstance(path_glob, str):
        path_glob = Path().glob(path_glob)

    # Coerce to list because we might need to use the sequence multiple times
    path_glob = sorted(list(path_glob))  # noqa: C414

    if not separate_times:
        return combine_datasets(path_glob, keep_particles=keep_particles)

    time_dims, var_times_map = make_time_dims(path_glob)
    all_dfs = [xr.open_dataset(f, keep_particles=keep_particles) for f in path_glob]

    for df in all_dfs:
        for da in df:
            df[da] = df[da].expand_dims(
                dim={var_times_map[str(da)]: [df.attrs["time"]]}
            )
        for coord in df.coords:
            if df.coords[coord].attrs.get("point_data", False):
                # We need to undo our renaming of the coordinates
                base_name = coord.split("_", maxsplit=1)[-1]
                sdf_coord_name = f"Grid_{base_name}"
                df.coords[coord] = df.coords[coord].expand_dims(
                    dim={var_times_map[sdf_coord_name]: [df.attrs["time"]]}
                )

    return xr.combine_by_coords(
        all_dfs, data_vars="minimal", combine_attrs="drop_conflicts"
    )


def make_time_dims(path_glob):
    """Extract the distinct set of time arrays from a collection of
    SDF files, along with a mapping from variable names to their time
    dimension.
    """
    # Map variable names to list of times
    vars_count = defaultdict(list)
    for f in path_glob:
        with SDFFile(str(f)) as sdf_file:
            for key in sdf_file.variables:
                vars_count[_rename_with_underscore(key)].append(sdf_file.header["time"])
            for grid in sdf_file.grids.values():
                vars_count[_rename_with_underscore(grid.name)].append(
                    sdf_file.header["time"]
                )

    # Count the unique set of lists of times
    times_count = Counter(tuple(v) for v in vars_count.values())

    # Give each set of times a unique name
    time_dims = {}
    for count, t in enumerate(times_count):
        time_dims[f"time{count}"] = t

    # Map each variable to the name of its time dimension
    var_times_map = {}
    for key, value in vars_count.items():
        v_tuple = tuple(value)
        for time_name, time_dim in time_dims.items():
            if v_tuple == time_dim:
                var_times_map[key] = time_name
                break
        else:
            raise ValueError(f"Didn't find time dim for {key!r} with {v_tuple}")

    return time_dims, var_times_map


class SDFBackendArray(BackendArray):
    """Adapater class required for lazy loading"""

    __slots__ = ("datastore", "dtype", "shape", "variable_name")

    def __init__(self, variable_name, datastore):
        self.datastore = datastore
        self.variable_name = variable_name

        array = self.get_array()
        self.shape = array.shape
        self.dtype = array.dtype

    def get_array(self, needs_lock=True):
        with self.datastore.acquire_context(needs_lock) as ds:
            return ds.variables[self.variable_name]

    def __getitem__(self, key: indexing.ExplicitIndexer) -> np.typing.ArrayLike:
        return indexing.explicit_indexing_adapter(
            key,
            self.shape,
            indexing.IndexingSupport.OUTER,
            self._raw_indexing_method,
        )

    def _raw_indexing_method(self, key: tuple) -> np.typing.ArrayLike:
        # thread safe method that access to data on disk
        with self.datastore.acquire_context():
            original_array = self.get_array(needs_lock=False)
            return original_array.data[key]


class SDFDataStore(AbstractDataStore):
    """Store for reading and writing data via the SDF library."""

    __slots__ = (
        "_filename",
        "_manager",
        "drop_variables",
        "keep_particles",
        "lock",
    )

    def __init__(self, manager, drop_variables=None, keep_particles=False, lock=None):
        self._manager = manager
        self._filename = self.ds.filename
        self.drop_variables = drop_variables
        self.keep_particles = keep_particles
        self.lock = ensure_lock(lock)

    @classmethod
    def open(
        cls,
        filename,
        lock=None,
        drop_variables=None,
        keep_particles=False,
    ):
        if isinstance(filename, os.PathLike):
            filename = os.fspath(filename)

        manager = CachingFileManager(SDFFile, filename, lock=lock)
        return cls(
            manager,
            lock=lock,
            drop_variables=drop_variables,
            keep_particles=keep_particles,
        )

    def _acquire(self, needs_lock=True):
        with self._manager.acquire_context(needs_lock) as ds:
            return ds

    @property
    def ds(self):
        return self._acquire()

    def acquire_context(self, needs_lock=True):
        return self._manager.acquire_context(needs_lock)

    def load(self):  # noqa: PLR0912, PLR0915
        # Drop any requested variables
        if self.drop_variables:
            for variable in self.drop_variables:
                # TODO: nicer error handling
                self.ds.variables.pop(variable)

        # These two dicts are global metadata about the run or file
        attrs = {**self.ds.header, **self.ds.run_info}

        data_vars = {}
        coords = {}

        def _norm_grid_name(grid_name: str) -> str:
            """There may be multiple grids all with the same coordinate names, so
            drop the "Grid/" from the start, and append the rest to the
            dimension name. This lets us disambiguate them all. Probably"""
            return grid_name.split("/", maxsplit=1)[-1]

        def _grid_species_name(grid_name: str) -> str:
            return grid_name.split("/")[-1]

        def _process_grid_name(grid_name: str, transform_func) -> str:
            """Apply the given transformation function and then rename with underscores."""
            transformed_name = transform_func(grid_name)
            return _rename_with_underscore(transformed_name)

        for key, value in self.ds.grids.items():
            if "cpu" in key.lower():
                # Had some problems with these variables, so just ignore them for now
                continue

            if not self.keep_particles and value.is_point_data:
                continue

            base_name = _process_grid_name(value.name, _norm_grid_name)

            for label, coord, unit in zip(value.labels, value.data, value.units):
                full_name = f"{label}_{base_name}"
                dim_name = (
                    f"ID_{_process_grid_name(key, _grid_species_name)}"
                    if value.is_point_data
                    else full_name
                )
                coords[full_name] = (
                    dim_name,
                    coord,
                    {
                        "long_name": label.replace("_", " "),
                        "units": unit,
                        "point_data": value.is_point_data,
                        "full_name": value.name,
                    },
                )

        # Read and convert SDF variables and meshes to xarray DataArrays and Coordinates
        for key, value in self.ds.variables.items():
            # Had some problems with these variables, so just ignore them for now
            if "cpu" in key.lower():
                continue
            if "boundary" in key.lower():
                continue
            if "output file" in key.lower():
                continue

            if not self.keep_particles and value.is_point_data:
                continue

            if isinstance(value, Constant) or value.grid is None:
                # We don't have a grid, either because it's just a
                # scalar, or because it's an array over something
                # else. We have no more information, so just make up
                # some (hopefully) unique dimension names
                shape = getattr(value.data, "shape", ())
                dims = [f"dim_{key}_{n}" for n, _ in enumerate(shape)]
                base_name = _rename_with_underscore(key)

                data_attrs = {}
                data_attrs["full_name"] = key
                data_attrs["long_name"] = base_name.replace("_", " ")
                if value.units is not None:
                    data_attrs["units"] = value.units

                data_vars[base_name] = Variable(dims, value.data, attrs=data_attrs)
                continue

            if value.is_point_data:
                # Point (particle) variables are 1D
                var_coords = (f"ID_{_process_grid_name(key, _grid_species_name)}",)
            else:
                # These are DataArrays

                # SDF makes matching up the coordinates a bit convoluted. Each
                # dimension on a variable can be defined either on "grid" or
                # "grid_mid", and the only way to tell which one is to compare the
                # variable's dimension sizes for each grid. We do this by making a
                # nested dict that looks something like:
                #
                #     {"X": {129: "X_Grid", 129: "X_Grid_mid"}}
                #
                # Then we can look up the dimension label and size to get *our* name
                # for the corresponding coordinate
                dim_size_lookup = defaultdict(dict)
                grid = self.ds.grids[value.grid]
                grid_base_name = _process_grid_name(grid.name, _norm_grid_name)
                for dim_size, dim_name in zip(grid.shape, grid.labels):
                    dim_size_lookup[dim_name][dim_size] = f"{dim_name}_{grid_base_name}"

                grid_mid = self.ds.grids[value.grid_mid]
                grid_mid_base_name = _process_grid_name(grid_mid.name, _norm_grid_name)
                for dim_size, dim_name in zip(grid_mid.shape, grid_mid.labels):
                    dim_size_lookup[dim_name][
                        dim_size
                    ] = f"{dim_name}_{grid_mid_base_name}"

                var_coords = [
                    dim_size_lookup[dim_name][dim_size]
                    for dim_name, dim_size in zip(grid.labels, value.shape)
                ]

            # TODO: error handling here? other attributes?
            base_name = _rename_with_underscore(key)
            long_name = _process_latex_name(base_name.replace("_", " "))
            data_attrs = {
                "units": value.units,
                "point_data": value.is_point_data,
                "full_name": key,
                "long_name": long_name,
            }
            lazy_data = indexing.LazilyIndexedArray(SDFBackendArray(key, self))
            data_vars[base_name] = Variable(var_coords, lazy_data, data_attrs)

        # TODO: might need to decode if mult is set?

        # #  see also conventions.decode_cf_variables
        # vars, attrs, coords = my_decode_variables(
        #     vars, attrs, decode_times, decode_timedelta, decode_coords
        # )

        ds = xr.Dataset(data_vars, attrs=attrs, coords=coords)
        ds.set_close(self.ds.close)

        return ds

    def close(self, **kwargs):
        self._manager.close(**kwargs)


class SDFEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        keep_particles=False,
    ):
        if isinstance(filename_or_obj, Path):
            # sdf library takes a filename only
            # TODO: work out if we need to deal with file handles
            filename_or_obj = str(filename_or_obj)

        store = SDFDataStore.open(
            filename_or_obj,
            drop_variables=drop_variables,
            keep_particles=keep_particles,
        )
        with close_on_error(store):
            return store.load()

    open_dataset_parameters: ClassVar[list[str]] = [
        "filename_or_obj",
        "drop_variables",
        "keep_particles",
    ]

    def guess_can_open(self, filename_or_obj):
        magic_number = try_read_magic_number_from_path(filename_or_obj)
        if magic_number is not None:
            return magic_number.startswith(b"SDF1")

        return Path(filename_or_obj).suffix in {".sdf", ".SDF"}

    description = "Use .sdf files in Xarray"

    url = "https://epochpic.github.io/documentation/visualising_output/python.html"


class SDFPreprocess:
    """Preprocess SDF files for xarray ensuring matching job ids and sets time dimension"""

    def __init__(self):
        self.job_id: int | None = None

    def __call__(self, ds: xr.Dataset) -> xr.Dataset:
        if self.job_id is None:
            self.job_id = ds.attrs["jobid1"]

        if self.job_id != ds.attrs["jobid1"]:
            raise ValueError(
                f"Mismatching job ids (got {ds.attrs['jobid1']}, expected {self.job_id})"
            )

        ds = ds.expand_dims(time=[ds.attrs["time"]])
        ds = ds.assign_coords(
            time=(
                "time",
                [ds.attrs["time"]],
                {"units": "s", "long_name": "Time", "full_name": "time"},
            )
        )
        # Particles' spartial coordinates also evolve in time
        for coord, value in ds.coords.items():
            if value.attrs.get("point_data", False):
                ds.coords[coord] = value.expand_dims(time=[ds.attrs["time"]])

        return ds
