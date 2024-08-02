import pathlib

import xarray as xr

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"


def test_basic():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as df:
        ex_field = "Electric Field/Ex"
        assert ex_field in df
        x_coord = "X_Grid_mid"
        assert x_coord in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"


def test_coords():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf") as df:
        px_electron = "dist_fn/x_px/electron"
        assert px_electron in df
        x_coord = "Px_x_px/electron"
        assert x_coord in df[px_electron].coords
        assert df[x_coord].attrs["long_name"] == "Px"
