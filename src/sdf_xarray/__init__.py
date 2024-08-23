import os
import pathlib
from collections import Counter, defaultdict
from typing import Iterable

import xarray as xr
from xarray.backends import BackendEntrypoint
from xarray.core.utils import try_read_magic_number_from_path

from . import sdf
from .sdf_interface import SDFFile as SDFFile, Constant


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
    path_glob: Iterable | str | pathlib.Path | pathlib.Path.glob,
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
        path_glob = pathlib.Path().glob(path_glob)

    # Coerce to list because we might need to use the sequence multiple times
    path_glob = sorted(list(path_glob))

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
            if "Particles" in coord:
                # We need to undo our renaming of the coordinates
                base_name = coord.split("_", maxsplit=1)[-1]
                sdf_coord_name = f"Grid/{base_name}"
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
        sdf_file = sdf.read(str(f), dict=True)
        for key in sdf_file:
            vars_count[key].append(sdf_file["Header"]["time"])

    # Count the unique set of lists of times
    times_count = Counter((tuple(v) for v in vars_count.values()))

    # Give each set of times a unique name
    time_dims = {}
    count = 0
    for t in times_count:
        time_dims[f"time{count}"] = t
        count += 1

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


def read_sdf_dataset(data: SDFFile, *, drop_variables=None, keep_particles=False):
    # Drop any requested variables
    if drop_variables:
        for variable in drop_variables:
            # TODO: nicer error handling
            data.variables.pop(variable)

    # These two dicts are global metadata about the run or file
    attrs = {**data.header, **data.run_info}

    data_vars = {}
    coords = {}

    def _norm_grid_name(grid_name: str) -> str:
        """There may be multiple grids all with the same coordinate names, so
        drop the "Grid/" from the start, and append the rest to the
        dimension name. This lets us disambiguate them all. Probably"""
        return grid_name.split("/", maxsplit=1)[-1]

    def _grid_species_name(grid_name: str) -> str:
        return grid_name.split("/")[-1]

    for key, value in data.grids.items():
        if "cpu" in key.lower():
            # Had some problems with these variables, so just ignore them for now
            continue

        base_name = _norm_grid_name(value.name)

        for label, coord, unit in zip(value.labels, value.data, value.units):
            full_name = f"{label}_{base_name}"
            dim_name = (
                f"ID_{_grid_species_name(key)}" if value.is_point_data else full_name
            )
            coords[full_name] = (
                dim_name,
                coord,
                {"long_name": label, "units": unit},
            )

    # Read and convert SDF variables and meshes to xarray DataArrays and Coordinates
    for key, value in data.variables.items():
        if "CPU" in key:
            # Had some problems with these variables, so just ignore them for now
            continue

        if not keep_particles and "particles" in key.lower():
            continue

        if isinstance(value, Constant):
            # This might have consequences when reading in multiple files?
            attrs[key] = value.data

        elif value.grid is None:
            # No grid, so not physical data, just stick it in as an attribute
            attrs[key] = value.data

        elif value.is_point_data:
            # Point (particle) variables are 1D
            var_coords = (f"ID_{_grid_species_name(key)}",)
            data_attrs = {"units": value.units}
            data_vars[key] = (var_coords, value.data, data_attrs)
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
            grid = data.grids[value.grid]
            grid_base_name = _norm_grid_name(grid.name)
            for dim_size, dim_name in zip(grid.dims, grid.labels):
                dim_size_lookup[dim_name][dim_size] = f"{dim_name}_{grid_base_name}"

            grid_mid = data.grids[value.grid_mid]
            grid_mid_base_name = _norm_grid_name(grid_mid.name)
            for dim_size, dim_name in zip(grid_mid.dims, grid_mid.labels):
                dim_size_lookup[dim_name][dim_size] = f"{dim_name}_{grid_mid_base_name}"

            var_coords = [
                dim_size_lookup[dim_name][dim_size]
                for dim_name, dim_size in zip(grid.labels, value.dims)
            ]
            # TODO: error handling here? other attributes?
            data_attrs = {"units": value.units}
            data_vars[key] = (var_coords, value.data, data_attrs)

    # TODO: might need to decode if mult is set?

    # #  see also conventions.decode_cf_variables
    # vars, attrs, coords = my_decode_variables(
    #     vars, attrs, decode_times, decode_timedelta, decode_coords
    # )

    ds = xr.Dataset(data_vars, attrs=attrs, coords=coords)
    # I think SDF basically keeps files open for the whole lifetime of the
    # Python block variables, so there's no way to explicitly close them
    ds.set_close(lambda: None)

    return ds


class SDFEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        keep_particles=False,
    ):
        if isinstance(filename_or_obj, pathlib.Path):
            # sdf library takes a filename only
            # TODO: work out if we need to deal with file handles
            filename_or_obj = str(filename_or_obj)

        with SDFFile(filename_or_obj) as data:
            return read_sdf_dataset(
                data, drop_variables=drop_variables, keep_particles=keep_particles
            )

    open_dataset_parameters = ["filename_or_obj", "drop_variables", "keep_particles"]

    def guess_can_open(self, filename_or_obj):
        magic_number = try_read_magic_number_from_path(filename_or_obj)
        if magic_number is not None:
            return magic_number.startswith(b"SDF1")

        try:
            _, ext = os.path.splitext(filename_or_obj)
        except TypeError:
            return False
        return ext in {".sdf", ".SDF"}

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

        # Particles' spartial coordinates also evolve in time
        for coord, value in ds.coords.items():
            if "Particles" in coord:
                ds.coords[coord] = value.expand_dims(time=[ds.attrs["time"]])

        return ds
