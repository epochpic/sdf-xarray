import pathlib

import xarray as xr


EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"


def test_basic():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as df:
        ex_field = "Electric Field/Ex"
        assert ex_field in df
        x_coord = "X_x_px_deltaf/electron_beam"
        assert x_coord in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"
