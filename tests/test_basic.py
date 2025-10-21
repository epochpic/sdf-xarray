import pathlib

import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr

from sdf_xarray import SDFPreprocess, _process_latex_name, _resolve_glob, open_mfdataset

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files_1D"
EXAMPLE_MISMATCHED_FILES_DIR = (
    pathlib.Path(__file__).parent / "example_mismatched_files"
)
EXAMPLE_ARRAYS_DIR = pathlib.Path(__file__).parent / "example_array_no_grids"
EXAMPLE_3D_DIST_FN = pathlib.Path(__file__).parent / "example_dist_fn"
EXAMPLE_2D_PARTICLE_DATA = pathlib.Path(__file__).parent / "example_two_probes_2D"


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

        time = df["time"]
        ex = df.isel(time=10)["Electric_Field_Ex"]
        ex_values = ex.values
        ex_x_coords = ex.coords["X_Grid_mid"].values
        time_values = np.array(
            [
                5.466993e-14,
                2.417504e-10,
                4.833915e-10,
                7.251419e-10,
                9.667830e-10,
                1.208533e-09,
                1.450175e-09,
                1.691925e-09,
                1.933566e-09,
                2.175316e-09,
                2.416958e-09,
            ]
        )

        expected_ex = np.array(
            [
                -3126528.47057157754898071289062500000000,
                -3249643.37612255383282899856567382812500,
                -6827013.11566223856061697006225585937500,
                -9350267.99022011645138263702392578125000,
                -1643592.58487333403900265693664550781250,
                -2044751.41207189299166202545166015625000,
                -4342811.34666103497147560119628906250000,
                -10420841.38402196019887924194335937500000,
                -7038801.83154528774321079254150390625000,
                781649.31791684380732476711273193359375,
                4476555.84853181242942810058593750000000,
                5873312.79385650344192981719970703125000,
                -95930.60501570138148963451385498046875,
                -8977898.96547995693981647491455078125000,
                -7951712.64987809769809246063232421875000,
                -5655667.11171338520944118499755859375000,
            ]
        )
        expected_ex_coords = np.array(
            [
                1.72522447e-05,
                5.17567340e-05,
                8.62612233e-05,
                1.20765713e-04,
                1.55270202e-04,
                1.89774691e-04,
                2.24279181e-04,
                2.58783670e-04,
                2.93288159e-04,
                3.27792649e-04,
                3.62297138e-04,
                3.96801627e-04,
                4.31306117e-04,
                4.65810606e-04,
                5.00315095e-04,
                5.34819585e-04,
            ]
        )
        npt.assert_allclose(time_values, time.values, rtol=1e-6)
        npt.assert_allclose(ex_values, expected_ex)
        npt.assert_allclose(ex_x_coords, expected_ex_coords)


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


def test_resolve_glob_from_string_pattern():
    pattern = str(EXAMPLE_FILES_DIR / "*.sdf")
    result = _resolve_glob(pattern)
    expected = sorted(EXAMPLE_FILES_DIR.glob("*.sdf"))
    assert result == expected


def test_resolve_glob_from_path_glob():
    pattern = EXAMPLE_FILES_DIR.glob("*.sdf")
    result = _resolve_glob(pattern)
    expected = sorted(EXAMPLE_FILES_DIR.glob("*.sdf"))
    assert result == expected


def test_resolve_glob_from_path_missing_glob():
    pattern = EXAMPLE_FILES_DIR
    with pytest.raises(TypeError):
        _resolve_glob(pattern)


def test_resolve_glob_from_path_list():
    pattern = [EXAMPLE_FILES_DIR / "0000.sdf"]
    result = _resolve_glob(pattern)
    expected = [EXAMPLE_FILES_DIR / "0000.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple():
    pattern = [EXAMPLE_FILES_DIR / "0000.sdf", EXAMPLE_FILES_DIR / "0001.sdf"]
    result = _resolve_glob(pattern)
    expected = [EXAMPLE_FILES_DIR / "0000.sdf", EXAMPLE_FILES_DIR / "0001.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple_unordered():
    pattern = [EXAMPLE_FILES_DIR / "0001.sdf", EXAMPLE_FILES_DIR / "0000.sdf"]
    result = _resolve_glob(pattern)
    expected = [EXAMPLE_FILES_DIR / "0000.sdf", EXAMPLE_FILES_DIR / "0001.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple_duplicates():
    pattern = [
        EXAMPLE_FILES_DIR / "0000.sdf",
        EXAMPLE_FILES_DIR / "0000.sdf",
        EXAMPLE_FILES_DIR / "0001.sdf",
    ]
    result = _resolve_glob(pattern)
    expected = [EXAMPLE_FILES_DIR / "0000.sdf", EXAMPLE_FILES_DIR / "0001.sdf"]
    assert result == expected


def test_xr_erroring_on_mismatched_jobid_files():
    with pytest.raises(ValueError):  # noqa: PT011
        xr.open_mfdataset(
            EXAMPLE_MISMATCHED_FILES_DIR.glob("*.sdf"),
            combine="nested",
            data_vars="minimal",
            coords="minimal",
            compat="override",
            join="outer",
            preprocess=SDFPreprocess(),
        )


def test_xr_multiple_files_data():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as df:
        ex = df.isel(time=10)["Electric_Field_Ex"]
        ex_values = ex.values
        ex_x_coords = ex.coords["X_Grid_mid"].values

        expected_ex = np.array(
            [
                -3126528.47057157754898071289062500000000,
                -3249643.37612255383282899856567382812500,
                -6827013.11566223856061697006225585937500,
                -9350267.99022011645138263702392578125000,
                -1643592.58487333403900265693664550781250,
                -2044751.41207189299166202545166015625000,
                -4342811.34666103497147560119628906250000,
                -10420841.38402196019887924194335937500000,
                -7038801.83154528774321079254150390625000,
                781649.31791684380732476711273193359375,
                4476555.84853181242942810058593750000000,
                5873312.79385650344192981719970703125000,
                -95930.60501570138148963451385498046875,
                -8977898.96547995693981647491455078125000,
                -7951712.64987809769809246063232421875000,
                -5655667.11171338520944118499755859375000,
            ]
        )
        expected_ex_coords = np.array(
            [
                1.72522447e-05,
                5.17567340e-05,
                8.62612233e-05,
                1.20765713e-04,
                1.55270202e-04,
                1.89774691e-04,
                2.24279181e-04,
                2.58783670e-04,
                2.93288159e-04,
                3.27792649e-04,
                3.62297138e-04,
                3.96801627e-04,
                4.31306117e-04,
                4.65810606e-04,
                5.00315095e-04,
                5.34819585e-04,
            ]
        )
        npt.assert_allclose(ex_values, expected_ex)
        npt.assert_allclose(ex_x_coords, expected_ex_coords)


def test_xr_time_dim():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR.glob("*.sdf"),
        join="outer",
        preprocess=SDFPreprocess(),
    ) as df:
        time = df["time"]
        assert time.units == "s"
        assert time.long_name == "Time"
        assert time.full_name == "time"

        time_values = np.array(
            [
                5.466993e-14,
                2.417504e-10,
                4.833915e-10,
                7.251419e-10,
                9.667830e-10,
                1.208533e-09,
                1.450175e-09,
                1.691925e-09,
                1.933566e-09,
                2.175316e-09,
                2.416958e-09,
            ]
        )

        npt.assert_allclose(time_values, time.values, rtol=1e-6)


def test_xr_latex_rename_variables():
    with xr.open_mfdataset(
        EXAMPLE_ARRAYS_DIR.glob("*.sdf"),
        join="outer",
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


def test_xr_arrays_with_no_grids():
    with xr.open_dataset(EXAMPLE_ARRAYS_DIR / "0001.sdf") as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (1,)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (8,)


def test_xr_arrays_with_no_grids_multifile():
    with xr.open_mfdataset(
        EXAMPLE_ARRAYS_DIR.glob("*.sdf"),
        join="outer",
        preprocess=SDFPreprocess(),
    ) as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (2, 1)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (2, 8)


def test_xr_3d_distribution_function():
    with xr.open_dataset(EXAMPLE_3D_DIST_FN / "0000.sdf") as df:
        distribution_function = "dist_fn_x_px_py_Electron"
        assert df[distribution_function].shape == (16, 20, 20)


def test_xr_drop_variables():
    with xr.open_dataset(
        EXAMPLE_FILES_DIR / "0000.sdf", drop_variables=["Electric_Field_Ex"]
    ) as df:
        assert "Electric_Field_Ex" not in df


def test_xr_drop_variables_multiple():
    with xr.open_dataset(
        EXAMPLE_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field_Ex", "Electric_Field_Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


def test_xr_drop_variables_original():
    with xr.open_dataset(
        EXAMPLE_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field/Ex", "Electric_Field/Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


def test_xr_drop_variables_mixed():
    with xr.open_dataset(
        EXAMPLE_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field/Ex", "Electric_Field_Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


def test_xr_erroring_drop_variables():
    with pytest.raises(KeyError):
        xr.open_dataset(
            EXAMPLE_FILES_DIR / "0000.sdf", drop_variables=["Electric_Field/E"]
        )


def test_xr_loading_multiple_probes():
    with xr.open_dataset(
        EXAMPLE_2D_PARTICLE_DATA / "0002.sdf",
        keep_particles=True,
        probe_names=["Electron_Front_Probe", "Electron_Back_Probe"],
    ) as df:
        assert "X_Probe_Electron_Front_Probe" in df.coords
        assert "X_Probe_Electron_Back_Probe" in df.coords
        assert "ID_Electron_Front_Probe_Px" in df.dims
        assert "ID_Electron_Back_Probe_Px" in df.dims


def test_xr_oading_one_probe_drop_second_probe():
    with xr.open_dataset(
        EXAMPLE_2D_PARTICLE_DATA / "0002.sdf",
        keep_particles=True,
        drop_variables=[
            "Electron_Back_Probe_Px",
            "Electron_Back_Probe_Py",
            "Electron_Back_Probe_Pz",
            "Electron_Back_Probe_weight",
        ],
        probe_names=["Electron_Front_Probe"],
    ) as df:
        assert "X_Probe_Electron_Front_Probe" in df.coords
        assert "ID_Electron_Front_Probe_Px" in df.dims
        assert "ID_Electron_Back_Probe_Px" not in df.dims
