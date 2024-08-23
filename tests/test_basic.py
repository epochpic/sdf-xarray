import pathlib

import xarray as xr
from sdf_xarray import open_mfdataset, SDFPreprocess
import pytest

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"
EXAMPLE_MISMATCHED_FILES_DIR = (
    pathlib.Path(__file__).parent / "example_mismatched_files"
)


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


def test_particles():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf", keep_particles=True) as df:
        px_protons = "Particles/Px/proton"
        assert px_protons in df
        x_coord = "X_Particles/proton"
        assert x_coord in df[px_protons].coords
        assert df[x_coord].attrs["long_name"] == "X"


def test_no_particles():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf", keep_particles=False) as df:
        px_protons = "Particles/Px/proton"
        assert px_protons not in df


def test_multiple_files_one_time_dim():
    df = open_mfdataset(EXAMPLE_FILES_DIR.glob("*.sdf"), keep_particles=True)
    ex_field = df["Electric Field/Ex"]
    assert sorted(ex_field.coords) == sorted(("X_Grid_mid", "time"))
    assert ex_field.shape == (11, 16)

    ez_field = df["Electric Field/Ez"]
    assert sorted(ez_field.coords) == sorted(("X_Grid_mid", "time"))
    assert ez_field.shape == (11, 16)

    px_protons = df["Particles/Px/proton"]
    assert sorted(px_protons.coords) == sorted(("X_Particles/proton", "time"))
    assert px_protons.shape == (11, 1920)

    px_protons = df["Particles/Weight/proton"]
    assert sorted(px_protons.coords) == sorted(("X_Particles/proton", "time"))
    assert px_protons.shape == (11, 1920)


def test_multiple_files_multiple_time_dims():
    df = open_mfdataset(
        EXAMPLE_FILES_DIR.glob("*.sdf"), separate_times=True, keep_particles=True
    )

    assert list(df["Electric Field/Ex"].coords) != list(df["Electric Field/Ez"].coords)
    assert df["Electric Field/Ex"].shape == (11, 16)
    assert df["Electric Field/Ez"].shape == (1, 16)
    assert df["Particles/Px/proton"].shape == (1, 1920)
    assert df["Particles/Weight/proton"].shape == (2, 1920)


def test_erroring_on_mismatched_jobid_files():
    with pytest.raises(ValueError):
        xr.open_mfdataset(
            EXAMPLE_MISMATCHED_FILES_DIR.glob("*.sdf"),
            combine="nested",
            data_vars="minimal",
            coords="minimal",
            compat="override",
            preprocess=SDFPreprocess(),
        )
