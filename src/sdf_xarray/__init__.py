import os
import pathlib
from collections import Counter, defaultdict
from typing import Iterable

import xarray as xr
from xarray.backends import BackendEntrypoint
from xarray.core.utils import try_read_magic_number_from_path

from . import sdf


def combine_datasets(path_glob: Iterable | str) -> xr.Dataset:
    """Combine all datasets using a single time dimension"""

    return xr.open_mfdataset(
        path_glob, preprocess=lambda ds: ds.expand_dims(time=[ds.attrs["time"]])
    )


def open_mfdataset(
    path_glob: Iterable | str | pathlib.Path | pathlib.Path.glob,
    separate_times: bool = False,
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

    """

    # TODO: This is not very robust, look at how xarray.open_mfdataset does it
    if isinstance(path_glob, str):
        path_glob = pathlib.Path().glob(path_glob)

    # Coerce to list because we might need to use the sequence multiple times
    path_glob = sorted(list(path_glob))

    if not separate_times:
        return combine_datasets(path_glob)

    time_dims, var_times_map = make_time_dims(path_glob)
    all_dfs = [xr.open_dataset(f) for f in path_glob]

    for df in all_dfs:
        for da in df:
            df[da] = df[da].expand_dims(
                dim={var_times_map[str(da)]: [df.attrs["time"]]}
            )

    return xr.merge(all_dfs)


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


def open_sdf_dataset(filename_or_obj, *, drop_variables=None):
    if isinstance(filename_or_obj, pathlib.Path):
        # sdf library takes a filename only
        # TODO: work out if we need to deal with file handles
        filename_or_obj = str(filename_or_obj)

    data = sdf.read(filename_or_obj, dict=True)

    # Drop any requested variables
    if drop_variables:
        for variable in drop_variables:
            # TODO: nicer error handling
            data.pop(variable)

    # These two dicts are global metadata about the run or file
    attrs = {}
    attrs.update(data.pop("Header", {}))
    attrs.update(data.pop("Run_info", {}))

    data_vars = {}
    coords = {}

    # Read and convert SDF variables and meshes to xarray DataArrays and Coordinates
    for key, value in data.items():
        if "CPU" in key:
            # Had some problems with these variables, so just ignore them for now
            continue

        if isinstance(value, sdf.BlockConstant):
            # This might have consequences when reading in multiple files?
            attrs[key] = value.data

        elif isinstance(value, sdf.BlockPlainMesh):
            # These are Coordinates

            # There may be multiple grids all with the same coordinate names, so
            # drop the "Grid/" from the start, and append the rest to the
            # dimension name. This lets us disambiguate them all. Probably
            base_name = key.split("/", maxsplit=1)[-1]

            for label, coord, unit in zip(value.labels, value.data, value.units):
                full_name = f"{label}_{base_name}"
                coords[full_name] = (
                    full_name,
                    coord,
                    {"long_name": label, "units": unit},
                )
        elif isinstance(value, sdf.BlockPlainVariable):
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

            # TODO: remove duplication with coords branch
            grid_base_name = value.grid.name.split("/", maxsplit=1)[-1]
            for dim_size, dim_name in zip(value.grid.dims, value.grid.labels):
                dim_size_lookup[dim_name][dim_size] = f"{dim_name}_{grid_base_name}"

            grid_mid_base_name = value.grid_mid.name.split("/", maxsplit=1)[-1]
            for dim_size, dim_name in zip(value.grid_mid.dims, value.grid_mid.labels):
                dim_size_lookup[dim_name][dim_size] = f"{dim_name}_{grid_mid_base_name}"

            var_coords = [
                dim_size_lookup[dim_name][dim_size]
                for dim_name, dim_size in zip(value.grid.labels, value.dims)
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
    ):
        return open_sdf_dataset(filename_or_obj, drop_variables=drop_variables)

    open_dataset_parameters = ["filename_or_obj", "drop_variables"]

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
    def __init__(self):
        self.job_id: int | None = None

    def __call__(self, ds: xr.Dataset) -> xr.Dataset:
        if self.job_id is None:
            self.job_id = ds.attrs["jobid1"]

        if self.job_id != ds.attrs["jobid1"]:
            raise ValueError(
                f"Mismatching job ids (got {ds.attrs['jobid1']}, expected {self.job_id})"
            )

        return ds.expand_dims(time=[ds.attrs["time"]])
