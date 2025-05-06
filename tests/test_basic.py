import pathlib

import pytest
import xarray as xr

from sdf_xarray import SDFPreprocess, _process_latex_name, open_mfdataset

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"
EXAMPLE_MISMATCHED_FILES_DIR = (
    pathlib.Path(__file__).parent / "example_mismatched_files"
)
EXAMPLE_ARRAYS_DIR = pathlib.Path(__file__).parent / "example_array_no_grids"
EXAMPLE_3D_DIST_FN = pathlib.Path(__file__).parent / "example_dist_fn"


def test_basic():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as df:
        ex_field = "Electric_Field_Ex"
        assert ex_field in df
        x_coord = "X_Grid_mid"
        assert x_coord in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"

        px_protons = "Particles_Px_proton"
        assert px_protons not in df
        x_coord = "X_Particles_proton"
        assert x_coord not in df.coords


def test_constant_name_and_units():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0000.sdf") as df:
        name = "Absorption_Total_Laser_Energy_Injected"
        full_name = "Absorption/Total Laser Energy Injected"
        assert name in df
        assert df[name].units == "J"
        assert df[name].attrs["full_name"] == full_name


def test_coords():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf") as df:
        px_electron = "dist_fn_x_px_electron"
        assert px_electron in df
        print(df[px_electron].coords)
        x_coord = "Px_x_px_electron"
        assert x_coord in df[px_electron].coords
        assert df[x_coord].attrs["full_name"] == "Grid/x_px/electron"


def test_particles():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf", keep_particles=True) as df:
        px_protons = "Particles_Px_proton"
        assert px_protons in df
        x_coord = "X_Particles_proton"
        assert x_coord in df[px_protons].coords
        assert df[x_coord].attrs["long_name"] == "X"


def test_no_particles():
    with xr.open_dataset(EXAMPLE_FILES_DIR / "0010.sdf", keep_particles=False) as df:
        px_protons = "Particles_Px_proton"
        assert px_protons not in df


def test_multiple_files_one_time_dim():
    with open_mfdataset(EXAMPLE_FILES_DIR.glob("*.sdf"), keep_particles=True) as df:
        ex_field = df["Electric_Field_Ex"]
        assert sorted(ex_field.coords) == sorted(("X_Grid_mid", "time"))
        assert ex_field.shape == (11, 16)

        ez_field = df["Electric_Field_Ez"]
        assert sorted(ez_field.coords) == sorted(("X_Grid_mid", "time"))
        assert ez_field.shape == (11, 16)

        px_protons = df["Particles_Px_proton"]
        assert sorted(px_protons.coords) == sorted(("X_Particles_proton", "time"))
        assert px_protons.shape == (11, 1920)

        px_protons = df["Particles_Weight_proton"]
        assert sorted(px_protons.coords) == sorted(("X_Particles_proton", "time"))
        assert px_protons.shape == (11, 1920)

        absorption = df["Absorption_Total_Laser_Energy_Injected"]
        assert tuple(absorption.coords) == ("time",)
        assert absorption.shape == (11,)


def test_multiple_files_multiple_time_dims():
    with open_mfdataset(
        EXAMPLE_FILES_DIR.glob("*.sdf"), separate_times=True, keep_particles=True
    ) as df:
        assert list(df["Electric_Field_Ex"].coords) != list(
            df["Electric_Field_Ez"].coords
        )
        assert df["Electric_Field_Ex"].shape == (11, 16)
        assert df["Electric_Field_Ez"].shape == (1, 16)
        assert df["Particles_Px_proton"].shape == (1, 1920)
        assert df["Particles_Weight_proton"].shape == (2, 1920)
        assert df["Absorption_Total_Laser_Energy_Injected"].shape == (11,)


def test_erroring_on_mismatched_jobid_files():
    with pytest.raises(ValueError):  # noqa: PT011
        xr.open_mfdataset(
            EXAMPLE_MISMATCHED_FILES_DIR.glob("*.sdf"),
            combine="nested",
            data_vars="minimal",
            coords="minimal",
            compat="override",
            preprocess=SDFPreprocess(),
        )


def test_time_dim_units():
    with xr.open_mfdataset(
        EXAMPLE_ARRAYS_DIR.glob("*.sdf"), preprocess=SDFPreprocess()
    ) as df:
        assert df["time"].units == "s"
        assert df["time"].long_name == "Time"
        assert df["time"].full_name == "time"


def test_latex_rename_variables():
    with xr.open_mfdataset(
        EXAMPLE_ARRAYS_DIR.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        keep_particles=True,
    ) as df:
        assert df["Electric_Field_Ex"].attrs["long_name"] == "Electric Field $E_x$"
        assert df["Electric_Field_Ey"].attrs["long_name"] == "Electric Field $E_y$"
        assert df["Electric_Field_Ez"].attrs["long_name"] == "Electric Field $E_z$"
        assert df["Magnetic_Field_Bx"].attrs["long_name"] == "Magnetic Field $B_x$"
        assert df["Magnetic_Field_By"].attrs["long_name"] == "Magnetic Field $B_y$"
        assert df["Magnetic_Field_Bz"].attrs["long_name"] == "Magnetic Field $B_z$"
        assert df["Current_Jx"].attrs["long_name"] == "Current $J_x$"
        assert df["Current_Jy"].attrs["long_name"] == "Current $J_y$"
        assert df["Current_Jz"].attrs["long_name"] == "Current $J_z$"
        assert (
            df["Particles_Px_Electron"].attrs["long_name"] == "Particles $P_x$ Electron"
        )
        assert (
            df["Particles_Py_Electron"].attrs["long_name"] == "Particles $P_y$ Electron"
        )
        assert (
            df["Particles_Pz_Electron"].attrs["long_name"] == "Particles $P_z$ Electron"
        )

        assert _process_latex_name("Example") == "Example"
        assert _process_latex_name("PxTest") == "PxTest"

        assert (
            df["Absorption_Fraction_of_Laser_Energy_Absorbed"].attrs["long_name"]
            == "Absorption Fraction of Laser Energy Absorbed"
        )
        assert (
            df["Derived_Average_Particle_Energy"].attrs["long_name"]
            == "Derived Average Particle Energy"
        )


def test_arrays_with_no_grids():
    with xr.open_dataset(EXAMPLE_ARRAYS_DIR / "0001.sdf") as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (1,)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (8,)


def test_arrays_with_no_grids_multifile():
    with xr.open_mfdataset(
        EXAMPLE_ARRAYS_DIR.glob("*.sdf"), preprocess=SDFPreprocess()
    ) as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (2, 1)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (2, 8)


def test_3d_distribution_function():
    with xr.open_dataset(EXAMPLE_3D_DIST_FN / "0000.sdf") as df:
        distribution_function = "dist_fn_x_px_py_Electron"
        assert df[distribution_function].shape == (16, 20, 20)
