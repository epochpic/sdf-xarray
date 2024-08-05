import pathlib

import xarray as xr
from sdf_xarray import open_mfdataset


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


def test_multiple_files_one_time_dim():
    df = open_mfdataset(EXAMPLE_FILES_DIR.glob("*.sdf"))
    ex_field = df["Electric Field/Ex"]
    assert sorted(ex_field.coords) == sorted(("X_Grid_mid", "time"))
    assert ex_field.shape == (11, 16)

    ez_field = df["Electric Field/Ez"]
    assert sorted(ez_field.coords) == sorted(("X_Grid_mid", "time"))
    assert ez_field.shape == (11, 16)


def test_multiple_files_multiple_time_dims():
    df = open_mfdataset(EXAMPLE_FILES_DIR.glob("*.sdf"), separate_times=True)

    assert list(df["Electric Field/Ex"].coords) != list(df["Electric Field/Ez"].coords)
    assert df["Electric Field/Ex"].shape == (11, 16)
    assert df["Electric Field/Ez"].shape == (1, 16)
