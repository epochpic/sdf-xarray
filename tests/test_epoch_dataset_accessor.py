import pathlib

import numpy as np
import pytest
import xarray as xr

from sdf_xarray import open_mfdataset

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files_3D"


def test_rescale_coords_X():
    multiplier = 1e3
    unit_label = "mm"

    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names="X_Grid_mid",
        )

        expected_x = ds["X_Grid_mid"].values * multiplier
        assert np.allclose(ds_rescaled["X_Grid_mid"].values, expected_x)
        assert ds_rescaled["X_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["X_Grid_mid"].attrs["long_name"] == "X"
        assert ds_rescaled["X_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        assert np.allclose(ds_rescaled["Y_Grid_mid"].values, ds["Y_Grid_mid"].values)
        assert ds_rescaled["Y_Grid_mid"].attrs["units"] == "m"
        assert ds_rescaled["Y_Grid_mid"].attrs["long_name"] == "Y"
        assert ds_rescaled["Y_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        assert np.allclose(ds_rescaled["Z_Grid_mid"].values, ds["Z_Grid_mid"].values)
        assert ds_rescaled["Z_Grid_mid"].attrs["units"] == "m"
        assert ds_rescaled["Z_Grid_mid"].attrs["long_name"] == "Z"
        assert ds_rescaled["Z_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"


def test_rescale_coords_X_Y():
    multiplier = 1e2
    unit_label = "cm"

    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names=["X_Grid_mid", "Y_Grid_mid"],
        )

        expected_x = ds["X_Grid_mid"].values * multiplier
        assert np.allclose(ds_rescaled["X_Grid_mid"].values, expected_x)
        assert ds_rescaled["X_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["X_Grid_mid"].attrs["long_name"] == "X"
        assert ds_rescaled["X_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        expected_y = ds["Y_Grid_mid"].values * multiplier
        assert np.allclose(ds_rescaled["Y_Grid_mid"].values, expected_y)
        assert ds_rescaled["Y_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["Y_Grid_mid"].attrs["long_name"] == "Y"
        assert ds_rescaled["Y_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        assert np.allclose(ds_rescaled["Z_Grid_mid"].values, ds["Z_Grid_mid"].values)
        assert ds_rescaled["Z_Grid_mid"].attrs["units"] == "m"
        assert ds_rescaled["Z_Grid_mid"].attrs["long_name"] == "Z"
        assert ds_rescaled["Z_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"


def test_rescale_coords_X_Y_tuple():
    multiplier = 1e2
    unit_label = "cm"

    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names=("X_Grid_mid", "Y_Grid_mid"),
        )

        expected_x = ds["X_Grid_mid"].values * multiplier
        assert np.allclose(ds_rescaled["X_Grid_mid"].values, expected_x)
        assert ds_rescaled["X_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["X_Grid_mid"].attrs["long_name"] == "X"
        assert ds_rescaled["X_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        expected_y = ds["Y_Grid_mid"].values * multiplier
        assert np.allclose(ds_rescaled["Y_Grid_mid"].values, expected_y)
        assert ds_rescaled["Y_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["Y_Grid_mid"].attrs["long_name"] == "Y"
        assert ds_rescaled["Y_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"

        assert np.allclose(ds_rescaled["Z_Grid_mid"].values, ds["Z_Grid_mid"].values)
        assert ds_rescaled["Z_Grid_mid"].attrs["units"] == "m"
        assert ds_rescaled["Z_Grid_mid"].attrs["long_name"] == "Z"
        assert ds_rescaled["Z_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"


def test_rescale_coords_attributes_copied():
    multiplier = 1e6
    unit_label = "µm"

    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names=["X_Grid_mid"],
        )

        assert ds_rescaled["X_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["X_Grid_mid"].attrs["long_name"] == "X"
        assert ds_rescaled["X_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"


def test_rescale_coords_non_existent_coord():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as ds:
        with pytest.raises(ValueError, match="Coordinate 'Time' not found"):
            ds.epoch.rescale_coords(
                multiplier=1.0,
                unit_label="s",
                coord_names="Time",
            )

        with pytest.raises(ValueError, match="Coordinate 'Bad_Coord' not found"):
            ds.epoch.rescale_coords(
                multiplier=1e6,
                unit_label="µm",
                coord_names=["X_Grid_mid", "Bad_Coord"],
            )


def test_rescale_coords_time():
    multiplier = 1e-15
    unit_label = "fs"

    with open_mfdataset(EXAMPLE_FILES_DIR.glob("*.sdf")) as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names="time",
        )

        expected_time = ds["time"].values * multiplier
        assert np.allclose(ds_rescaled["time"].values, expected_time)
        assert ds_rescaled["time"].attrs["units"] == unit_label
        assert ds_rescaled["time"].attrs["long_name"] == "Time"
        assert ds_rescaled["time"].attrs["full_name"] == "time"
