import contextlib
import os
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from importlib.metadata import version
from itertools import product
from os import PathLike as os_PathLike
from pathlib import Path
from typing import ClassVar

import numpy as np
import xarray as xr
from packaging.version import Version
from xarray.backends import AbstractDataStore, BackendArray, BackendEntrypoint
from xarray.backends.file_manager import CachingFileManager
from xarray.backends.locks import ensure_lock
from xarray.core import indexing
from xarray.core.types import T_Chunks
from xarray.core.utils import close_on_error, try_read_magic_number_from_path
from xarray.core.variable import Variable

# NOTE: Do not delete these lines, otherwise the "epoch" dataset and dataarray
# accessors will not be imported when the user imports sdf_xarray
import sdf_xarray.dataset_accessor
import sdf_xarray.download
import sdf_xarray.plotting  # noqa: F401

# NOTE: This attempts to initialise with the "pint" accessor if the user
# has installed the package
with contextlib.suppress(ImportError):
    import pint_xarray  # noqa: F401

from .sdf_interface import Constant, SDFFile  # type: ignore  # noqa: PGH003

# TODO Remove this once the new kwarg options are fully implemented
if Version(version("xarray")) >= Version("2025.8.0"):
    xr.set_options(use_new_combine_kwarg_defaults=True)

PathLike = str | os_PathLike


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


def _resolve_glob(path_glob: PathLike | Iterable[PathLike]):
    """
    Normalise input path_glob into a sorted list of absolute, resolved Path objects.
    """

    try:
        p = Path(path_glob)
        paths = list(p.parent.glob(p.name)) if p.name == "*.sdf" else list(p)
    except TypeError:
        paths = list({Path(p) for p in path_glob})

    paths = sorted(p.resolve() for p in paths)
    if not paths:
        raise FileNotFoundError(f"No files matched pattern or input: {path_glob!r}")
    return paths


def _build_datatree_from_dataset(
    ds: xr.Dataset,
) -> xr.DataTree:
    """
    An `xarray.DataTree` is constructed utilising the original names in the SDF
    file. This is due to the fact that these names include slashes which `xarray`
    can use to automatically build up a datatree. We do additionally replace
    spaces with underscores to be more pythonic. You can find the
    `xarray.Dataset` name under the ``attrs["flat_structure_name"]`` for referencing.

    In some cases the user may output the ``always + species`` dumpmask which
    means that SDF variable will have species data plus a general one. When
    defining a `xarray.DataTree` you cannot have a node of that tree contain both
    variable information and have leaves with variables so we move the node
    information to a leaf named ``node/All`` (see example of
    ``Dervied/Number_Density/All`` in below table)

    Below are some examples of how variable names are translated from the
    regular `xarray.open_dataset` result into their more traditional names.

    =================================== ===================================
    Dataset variable name               DataTree variable name
    =================================== ===================================
    ``Derived_Number_Density``          ``Derived/Number_Density/All``
    ``Derived_Number_Density_Electron`` ``Derived/Number_Density/Electron``
    ``Derived_Number_Density_Ion``      ``Derived/Number_Density/Ion``
    ``Derived_Number_Density_Photon``   ``Derived/Number_Density/Photon``
    ``Derived_Average_Particle_Energy`` ``Derived/Average_Particle_Energy``
    =================================== ===================================

    Parameters
    ----------
    ds
        Incoming `xarray.Dataset` to convert to a `xarray.DataTree`
    """
    renames = {}
    for name, var in ds.data_vars.items():
        # Append the current variable name to the attributes
        var.attrs["flat_structure_name"] = name
        renames.update({name: var.attrs["full_name"].replace(" ", "_")})

    new_names = renames.values()

    final_renames = {
        key: (
            f"{path}/All"
            if any(other.startswith(f"{path}/") for other in new_names)
            else path
        )
        for key, path in renames.items()
    }

    ds = ds.rename_vars(final_renames)

    return xr.DataTree.from_dict(ds)


def purge_unselected_data_vars(ds: xr.Dataset, data_vars: list[str]) -> xr.Dataset:
    """
    If the user has exclusively requested only certain variables be
    loaded in then we purge all other variables and dimensions
    """
    existing_data_vars = set(ds.data_vars.keys())
    vars_to_keep = set(data_vars) & existing_data_vars
    vars_to_drop = existing_data_vars - vars_to_keep
    ds = ds.drop_vars(vars_to_drop)

    existing_dims = set(ds.sizes)
    dims_to_keep = set()
    for var in vars_to_keep:
        dims_to_keep.update(ds[var].coords._names)
        dims_to_keep.update(ds[var].dims)

    coords_to_drop = existing_dims - dims_to_keep
    return ds.drop_dims(coords_to_drop)


def combine_datasets(
    path_glob: Iterable | str, data_vars: list[str], **kwargs
) -> xr.Dataset:
    """
    Combine all datasets using a single time dimension, optionally extract
    data from only the listed data_vars
    """

    if data_vars is not None:
        return xr.open_mfdataset(
            path_glob,
            join="outer",
            coords="different",
            compat="no_conflicts",
            combine="nested",
            concat_dim="time",
            preprocess=SDFPreprocess(data_vars=data_vars),
            **kwargs,
        )

    return xr.open_mfdataset(
        path_glob,
        data_vars="all",
        coords="different",
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
        **kwargs,
    )


def open_mfdataset(
    path_glob: Iterable | str | Path | Callable[..., Iterable[Path]],
    *,
    separate_times: bool = False,
    keep_particles: bool = False,
    probe_names: list[str] | None = None,
    data_vars: list[str] | None = None,
    chunks: T_Chunks = "auto",
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
    probe_names :
        List of EPOCH probe names
    data_vars :
        List of data vars to load in (If not specified loads in all variables)
    chunks :
        Dictionary with keys given by dimension names and values given by chunk sizes.
        In general, these should divide the dimensions of each dataset. By default
        chunks are automatically set so that they are the same size as the dimensions
        stored in each of the SDF files. See `Xarray chunking-and-performance
        <https://docs.xarray.dev/en/stable/user-guide/dask.html#chunking-and-performance>`_
        for details on why this is useful for large datasets. The default behaviour is
        to do this automatically and can be disabled by ``chunks=None``.
    """

    path_glob = _resolve_glob(path_glob)

    if not separate_times:
        return combine_datasets(
            path_glob,
            data_vars=data_vars,
            keep_particles=keep_particles,
            probe_names=probe_names,
            chunks=chunks,
        )

    _, var_times_map = make_time_dims(path_glob)

    all_dfs = []
    for f in path_glob:
        ds = xr.open_dataset(
            f, keep_particles=keep_particles, probe_names=probe_names, chunks=chunks
        )

        # If the data_vars are specified then only load them in and disregard the rest.
        # If there are no remaining data variables then skip adding the dataset to list
        if data_vars is not None:
            ds = purge_unselected_data_vars(ds, data_vars)
            if not ds.data_vars:
                continue

        all_dfs.append(ds)

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
        all_dfs,
        coords="different",
        combine_attrs="drop_conflicts",
        join="outer",
        compat="no_conflicts",
    )


def open_datatree(
    path: PathLike,
    *,
    keep_particles: bool = False,
    probe_names: list[str] | None = None,
) -> xr.DataTree:
    """
    An `xarray.DataTree` is constructed utilising the original names in the SDF
    file. This is due to the fact that these names include slashes which `xarray`
    can use to automatically build up a datatree. We do additionally replace
    spaces with underscores to be more pythonic. You can find the
    `xarray.Dataset` name under the ``attrs["flat_structure_name"]`` for referencing.

    In some cases the user may output the ``always + species`` dumpmask which
    means that SDF variable will have species data plus a general one. When
    defining a `xarray.DataTree` you cannot have a node of that tree contain both
    variable information and have leaves with variables so we move the node
    information to a leaf named ``node/All`` (see example of
    ``Dervied/Number_Density/All`` in below table)

    Below are some examples of how variable names are translated from the
    regular `xarray.open_dataset` result into their more traditional names.

    =================================== ===================================
    Dataset variable name               DataTree variable name
    =================================== ===================================
    ``Derived_Number_Density``          ``Derived/Number_Density/All``
    ``Derived_Number_Density_Electron`` ``Derived/Number_Density/Electron``
    ``Derived_Number_Density_Ion``      ``Derived/Number_Density/Ion``
    ``Derived_Number_Density_Photon``   ``Derived/Number_Density/Photon``
    ``Derived_Average_Particle_Energy`` ``Derived/Average_Particle_Energy``
    =================================== ===================================

    Parameters
    ----------
    path
        The path to the SDF file
    keep_particles
        If ``True``, also load particle data (this may use a lot of memory!)
    probe_names
        List of EPOCH probe names

    Examples
    --------
    >>> dt = open_datatree("0000.sdf")
    >>> dt["Electric_Field"]["Ex"].values  # Access all Electric_Field_Ex data
    """

    return xr.open_datatree(
        path, keep_particles=keep_particles, probe_names=probe_names
    )


def open_mfdatatree(
    path_glob: Iterable | str | Path | Callable[..., Iterable[Path]],
    *,
    separate_times: bool = False,
    keep_particles: bool = False,
    probe_names: list[str] | None = None,
    data_vars: list[str] | None = None,
) -> xr.DataTree:
    """Open a set of EPOCH SDF files as one `xarray.DataTree`

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

    An `xarray.DataTree` is constructed utilising the original names in the SDF
    file. This is due to the fact that these names include slashes which `xarray`
    can use to automatically build up a datatree. We do additionally replace
    spaces with underscores to be more pythonic. You can find the
    `xarray.Dataset` name under the ``attrs["flat_structure_name"]`` for referencing.

    This function combines multiple SDF files into a single `xarray.DataTree` with a
    unified time dimension and hierarchical organization of variables.

    In some cases the user may output the ``always + species`` dumpmask which
    means that SDF variable will have species data plus a general one. When
    defining a `xarray.DataTree` you cannot have a node of that tree contain both
    variable information and have leaves with variables so we move the node
    information to a leaf named ``node/All`` (see example of
    ``Dervied/Number_Density/All`` in below table)

    Below are some examples of how variable names are translated from the
    regular `xarray.open_dataset` result into their more traditional names.

    =================================== ===================================
    Dataset variable name               DataTree variable name
    =================================== ===================================
    ``Derived_Number_Density``          ``Derived/Number_Density/All``
    ``Derived_Number_Density_Electron`` ``Derived/Number_Density/Electron``
    ``Derived_Number_Density_Ion``      ``Derived/Number_Density/Ion``
    ``Derived_Number_Density_Photon``   ``Derived/Number_Density/Photon``
    ``Derived_Average_Particle_Energy`` ``Derived/Average_Particle_Energy``
    =================================== ===================================

    Parameters
    ----------
    path_glob
        List of filenames or string glob pattern
    separate_times
        If ``True``, create separate time dimensions for variables defined at
        different output frequencies
    keep_particles
        If ``True``, also load particle data (this may use a lot of memory!)
    probe_names
        List of EPOCH probe names
    data_vars
        List of data vars to load in (If not specified loads in all variables)

    Examples
    --------
    >>> dt = open_mfdatatree("*.sdf")
    >>> dt["Electric_Field"]["Ex"].values  # Access all Electric_Field_Ex data
    >>> dt.coords["time"].values  # Access combined time dimension
    """
    # First, combine the datasets as usual
    combined_ds = open_mfdataset(
        path_glob,
        separate_times=separate_times,
        keep_particles=keep_particles,
        probe_names=probe_names,
        data_vars=data_vars,
    )

    return _build_datatree_from_dataset(combined_ds)


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

    def __init__(self, variable_name, datastore, shape, dtype):
        self.datastore = datastore
        self.variable_name = variable_name
        self.shape = shape
        self.dtype = dtype

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
        "probe_names",
    )

    def __init__(
        self,
        manager,
        drop_variables=None,
        keep_particles=False,
        lock=None,
        probe_names=None,
    ):
        self._manager = manager
        self._filename = self.ds.filename
        self.drop_variables = drop_variables
        self.keep_particles = keep_particles
        self.lock = ensure_lock(lock)
        self.probe_names = probe_names

    @classmethod
    def open(
        cls,
        filename,
        lock=None,
        drop_variables=None,
        keep_particles=False,
        probe_names=None,
    ):
        if isinstance(filename, os.PathLike):
            filename = os.fspath(filename)

        manager = CachingFileManager(SDFFile, filename, lock=lock)
        return cls(
            manager,
            lock=lock,
            drop_variables=drop_variables,
            keep_particles=keep_particles,
            probe_names=probe_names,
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
            # Build a mapping from underscored names to real variable names
            name_map = {_rename_with_underscore(var): var for var in self.ds.variables}

            for variable in self.drop_variables:
                key = _rename_with_underscore(variable)
                original_name = name_map.get(key)

                if original_name is None:
                    raise KeyError(
                        f"Variable '{variable}' not found (interpreted as '{key}')."
                    )
                self.ds.variables.pop(original_name)

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

                var = Variable(dims, value.data, attrs=data_attrs)

                # Provide preferred_chunks for constants so dask aligns to natural shapes
                var.encoding["preferred_chunks"] = dict(zip(dims, shape))

                data_vars[base_name] = var
                continue

            if value.is_point_data:
                # Point (particle) variables are 1D

                # Particle data does not maintain a fixed dimension size
                # throughout the simulation. An example of a particle name comes
                # in the form of `Particles/Px/Ion_H` which is then modified
                # using `_process_grid_name()` into `Ion_H`. This is fine as the
                # other components of the momentum (`Py`, `Pz`) will have the same
                # size as they represent the same bunch of particles.

                # Probes however have names in the form of `Electron_Front_Probe/Px`
                # which are changed to just `Px`; this is fine when there is only one
                # probe in the system but when there are multiple they will have
                # conflicting sizes so we can't keep the names as simply `Px` so we
                # instead set their dimension as the full name `Electron_Front_Probe_Px`.
                is_probe_name_match = self.probe_names is not None and any(
                    name in key for name in self.probe_names
                )
                name_processor = (
                    _rename_with_underscore
                    if is_probe_name_match
                    else _grid_species_name
                )
                var_coords = (f"ID_{_process_grid_name(key, name_processor)}",)
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
            lazy_data = indexing.LazilyIndexedArray(
                SDFBackendArray(key, self, shape=value.shape, dtype=value.data.dtype)
            )
            var = Variable(var_coords, lazy_data, data_attrs)
            # Set preferred chunks to match on-disk layout
            # For point data (1D): full dimension
            # For grid data (N-D): individual grid chunk sizes
            if value.is_point_data:
                var.encoding["preferred_chunks"] = {var_coords[0]: len(value.data)}
            else:
                # Align with on-disk grid structure
                chunk_dict = {}
                for dim_name, size in zip(var_coords, value.shape):
                    # Use natural on-disk boundaries
                    chunk_dict[dim_name] = size
                var.encoding["preferred_chunks"] = chunk_dict

            data_vars[base_name] = var

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
    supports_groups = True
    open_dataset_parameters: ClassVar[list[str]] = [
        "filename_or_obj",
        "drop_variables",
        "keep_particles",
        "probe_names",
    ]

    def open_dataset(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        keep_particles=False,
        probe_names=None,
    ):
        if isinstance(filename_or_obj, Path):
            # sdf library takes a filename only
            # TODO: work out if we need to deal with file handles
            filename_or_obj = str(filename_or_obj)

        store = SDFDataStore.open(
            filename_or_obj,
            drop_variables=drop_variables,
            keep_particles=keep_particles,
            probe_names=probe_names,
        )
        with close_on_error(store):
            return store.load()

    open_datatree_parameters: ClassVar[list[str]] = [
        "filename_or_obj",
        "drop_variables",
        "keep_particles",
        "probe_names",
    ]

    def open_datatree(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        keep_particles=False,
        probe_names=None,
    ):
        ds = self.open_dataset(
            filename_or_obj,
            drop_variables=drop_variables,
            keep_particles=keep_particles,
            probe_names=probe_names,
        )
        return _build_datatree_from_dataset(ds)

    def guess_can_open(self, filename_or_obj):
        magic_number = try_read_magic_number_from_path(filename_or_obj)
        if magic_number is not None:
            return magic_number.startswith(b"SDF1")

        return Path(filename_or_obj).suffix in {".sdf", ".SDF"}

    description = "Use .sdf files in Xarray"

    url = "https://epochpic.github.io/documentation/visualising_output/python_beam.html"


class SDFPreprocess:
    """Preprocess SDF files for xarray ensuring matching job ids and sets
    time dimension.

    This class is used as a 'preprocess' function within ``xr.open_mfdataset``. It
    performs three main duties on each individual file's Dataset:

    1. Checks for a **matching job ID** across all files to ensure dataset consistency.
    2. **Filters** the Dataset to keep only the variables specified in `data_vars`
       and their required coordinates.
    3. **Expands dimensions** to include a single 'time' coordinate, preparing the
       Dataset for concatenation.

    EPOCH can output variables at different intervals, so some SDF files
    may not contain the requested variable. We combine this data into one
    dataset by concatenating across the time dimension.

    The combination is performed using ``join="outer"`` (in the calling ``open_mfdataset`` function),
    meaning that the final combined dataset will contain the variable across the
    entire time span, with NaNs filling the time steps where the variable was absent in
    the individual file.

    With large SDF files, this filtering method will save on memory consumption when
    compared to loading all variables from all files before concatenation.

    Parameters
    ----------
    data_vars :
        A list of data variables to load in (If not specified loads
        in all variables)
    """

    def __init__(
        self,
        data_vars: list[str] | None = None,
    ):
        self.job_id: int | None = None
        self.data_vars = data_vars

    def __call__(self, ds: xr.Dataset) -> xr.Dataset:
        if self.job_id is None:
            self.job_id = ds.attrs["jobid1"]

        if self.job_id != ds.attrs["jobid1"]:
            raise ValueError(
                f"Mismatching job ids (got {ds.attrs['jobid1']}, expected {self.job_id})"
            )

        # If the user has exclusively requested only certain variables be
        # loaded in then we purge all other variables and coordinates
        if self.data_vars:
            ds = purge_unselected_data_vars(ds, self.data_vars)

        time_val = ds.attrs.get("time", np.nan)
        ds = ds.expand_dims(time=[time_val])
        ds = ds.assign_coords(
            time=(
                "time",
                [time_val],
                {"units": "s", "long_name": "Time", "full_name": "time"},
            )
        )
        # Particles' spartial coordinates also evolve in time
        for coord, value in ds.coords.items():
            if value.attrs.get("point_data", False):
                ds.coords[coord] = value.expand_dims(time=[time_val])

        return ds
