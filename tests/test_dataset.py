from typing import Protocol

import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr

import sdf_xarray as sdfxr
from sdf_xarray import (
    SDFPreprocess,
    _process_latex_name,
    _resolve_glob,
    download,
)

TEST_FILES_DIR = download.fetch_dataset("test_files_1D")
TEST_MISMATCHED_FILES_DIR = download.fetch_dataset("test_mismatched_files")
TEST_ARRAYS_DIR = download.fetch_dataset("test_array_no_grids")
TEST_3D_DIST_FN = download.fetch_dataset("test_dist_fn")
TEST_2D_PARTICLE_DATA = download.fetch_dataset("test_two_probes_2D")


# Type hinting support
class XRLibrary(Protocol):
    def open_dataset(self, *args, **kwargs) -> xr.Dataset: ...

    def open_mfdataset(self, *args, **kwargs) -> xr.Dataset: ...


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_basic(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf") as df:
        ex_field = "Electric_Field_Ex"
        assert ex_field in df
        x_coord = "X_Grid_mid"
        assert x_coord in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"

        px_protons = "Particles_Px_proton"
        assert px_protons not in df
        x_coord = "X_Particles_proton"
        assert x_coord not in df.coords


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_constant_name_and_units(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf") as df:
        name = "Absorption_Total_Laser_Energy_Injected"
        full_name = "Absorption/Total Laser Energy Injected"
        assert name in df
        assert df[name].units == "J"
        assert df[name].attrs["full_name"] == full_name


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_preferred_chunks_metadata(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf") as df:
        for var in df.data_vars:
            assert "preferred_chunks" in df[var].encoding


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_coords(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0010.sdf") as df:
        px_electron = "dist_fn_x_px_electron"
        assert px_electron in df
        x_coord = "Px_x_px_electron"
        assert x_coord in df[px_electron].coords
        assert df[x_coord].attrs["full_name"] == "Grid/x_px/electron"


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_particles(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0010.sdf", keep_particles=True) as df:
        px_protons = "Particles_Px_proton"
        assert px_protons in df
        x_coord = "X_Particles_proton"
        assert x_coord in df[px_protons].coords
        assert df[x_coord].attrs["long_name"] == "X"


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_no_particles(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0010.sdf", keep_particles=False) as df:
        px_protons = "Particles_Px_proton"
        assert px_protons not in df


@pytest.mark.parametrize(
    ("xrlib", "params"),
    [
        (
            xr,
            {
                "compat": "no_conflicts",
                "join": "outer",
                "preprocess": SDFPreprocess(),
            },
        ),
        (sdfxr, {}),
    ],
)
def test_multiple_files_one_time_dim(xrlib: XRLibrary, params):
    with xrlib.open_mfdataset(
        paths=TEST_FILES_DIR.glob("*.sdf"),
        keep_particles=True,
        **params,
    ) as df:
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
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"), separate_times=True, keep_particles=True
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
    pattern = str(TEST_FILES_DIR / "*.sdf")
    result = _resolve_glob(pattern)
    expected = sorted(TEST_FILES_DIR.glob("*.sdf"))
    assert result == expected


def test_resolve_glob_from_path_glob():
    pattern = TEST_FILES_DIR.glob("*.sdf")
    result = _resolve_glob(pattern)
    expected = sorted(TEST_FILES_DIR.glob("*.sdf"))
    assert result == expected


def test_resolve_glob_from_path_missing_glob():
    pattern = TEST_FILES_DIR
    with pytest.raises(TypeError):
        _resolve_glob(pattern)


def test_resolve_glob_from_path_list():
    pattern = [TEST_FILES_DIR / "0000.sdf"]
    result = _resolve_glob(pattern)
    expected = [TEST_FILES_DIR / "0000.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple():
    pattern = [TEST_FILES_DIR / "0000.sdf", TEST_FILES_DIR / "0001.sdf"]
    result = _resolve_glob(pattern)
    expected = [TEST_FILES_DIR / "0000.sdf", TEST_FILES_DIR / "0001.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple_unordered():
    pattern = [TEST_FILES_DIR / "0001.sdf", TEST_FILES_DIR / "0000.sdf"]
    result = _resolve_glob(pattern)
    expected = [TEST_FILES_DIR / "0000.sdf", TEST_FILES_DIR / "0001.sdf"]
    assert result == expected


def test_resolve_glob_from_path_list_multiple_duplicates():
    pattern = [
        TEST_FILES_DIR / "0000.sdf",
        TEST_FILES_DIR / "0000.sdf",
        TEST_FILES_DIR / "0001.sdf",
    ]
    result = _resolve_glob(pattern)
    expected = [TEST_FILES_DIR / "0000.sdf", TEST_FILES_DIR / "0001.sdf"]
    assert result == expected


@pytest.mark.parametrize(
    ("xrlib", "params"),
    [
        (
            xr,
            {
                "compat": "no_conflicts",
                "join": "outer",
                "preprocess": SDFPreprocess(),
            },
        ),
        (sdfxr, {}),
    ],
)
def test_erroring_on_mismatched_jobid_files(xrlib, params):
    with pytest.raises(ValueError):  # noqa: PT011
        xrlib.open_mfdataset(paths=TEST_MISMATCHED_FILES_DIR.glob("*.sdf"), **params)


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_latex_rename_variables(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_ARRAYS_DIR / "0001.sdf", keep_particles=True) as df:
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
    with xr.open_dataset(TEST_ARRAYS_DIR / "0001.sdf") as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (1,)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (8,)


def test_arrays_with_no_grids_multifile():
    with xr.open_mfdataset(
        TEST_ARRAYS_DIR.glob("*.sdf"),
        join="outer",
        preprocess=SDFPreprocess(),
    ) as df:
        laser_phase = "laser_x_min_phase"
        assert laser_phase in df
        assert df[laser_phase].shape == (1, 1)

        random_states = "Random_States"
        assert random_states in df
        assert df[random_states].shape == (1, 8)


def test_3d_distribution_function():
    with xr.open_dataset(TEST_3D_DIST_FN / "0000.sdf") as df:
        distribution_function = "dist_fn_x_px_py_Electron"
        assert df[distribution_function].shape == (16, 20, 20)


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_drop_variables(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf", drop_variables=["Electric_Field_Ex"]
    ) as df:
        assert "Electric_Field_Ex" not in df


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_drop_variables_multiple(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field_Ex", "Electric_Field_Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_drop_variables_original(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field/Ex", "Electric_Field/Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_drop_variables_mixed(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf",
        drop_variables=["Electric_Field/Ex", "Electric_Field_Ey"],
    ) as df:
        assert "Electric_Field_Ex" not in df
        assert "Electric_Field_Ey" not in df


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_erroring_drop_variables(xrlib: XRLibrary):
    with pytest.raises(KeyError):
        xrlib.open_dataset(
            TEST_FILES_DIR / "0000.sdf", drop_variables=["Electric_Field/E"]
        )


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_loading_multiple_probes(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_2D_PARTICLE_DATA / "0002.sdf",
        keep_particles=True,
        probe_names=["Electron_Front_Probe", "Electron_Back_Probe"],
    ) as df:
        assert "X_Probe_Electron_Front_Probe" in df.coords
        assert "X_Probe_Electron_Back_Probe" in df.coords
        assert "ID_Electron_Front_Probe_Px" in df.dims
        assert "ID_Electron_Back_Probe_Px" in df.dims


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_loading_one_probe_drop_second_probe(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_2D_PARTICLE_DATA / "0002.sdf",
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


def test_open_mfdataset_data_vars_single():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex"],
    ) as df:
        ex_field = "Electric_Field_Ex"
        x_coord = "X_Grid_mid"
        assert ex_field in df
        assert x_coord in df[ex_field].coords
        assert "time" in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"

        assert "Electric_Field_Ey" not in df


def test_open_mfdataset_data_vars_multiple():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Electric_Field_Ey"],
    ) as df:
        ex_field = "Electric_Field_Ex"
        x_coord = "X_Grid_mid"
        assert ex_field in df
        assert x_coord in df[ex_field].coords
        assert "time" in df[ex_field].coords
        assert df[x_coord].attrs["long_name"] == "X"

        ey_field = "Electric_Field_Ey"
        x_coord = "X_Grid_mid"
        assert ey_field in df
        assert x_coord in df[ey_field].coords
        assert "time" in df[ey_field].coords
        assert df[x_coord].attrs["long_name"] == "X"


def test_open_mfdataset_data_vars_sparse_multiple():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        keep_particles=True,
        data_vars=[
            "Particles_Particles_Per_Cell_proton",
            "Electric_Field_Ez",
            "dist_fn_x_px_proton",
        ],
    ) as df:
        ppc_proton = "Particles_Particles_Per_Cell_proton"
        assert ppc_proton in df
        assert "time" in df[ppc_proton].coords
        assert (
            df[ppc_proton].attrs["long_name"] == "Particles Particles Per Cell proton"
        )

        ez_field = "Electric_Field_Ez"
        assert ez_field in df
        assert len(df[ez_field].coords) == 2
        assert "time" in df[ez_field].coords
        assert "X_Grid_mid" in df[ez_field].coords
        assert df[ez_field].attrs["long_name"] == "Electric Field $E_z$"

        dist_fn = "dist_fn_x_px_proton"
        assert dist_fn in df
        assert len(df[dist_fn].coords) == 3
        assert "time" in df[dist_fn].coords
        assert "X_x_px_proton" in df[dist_fn].coords
        assert "Px_x_px_proton" in df[dist_fn].coords

        assert df["time"].size == 11


def test_open_mfdataset_data_vars_invalid_var():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field"],
    ) as df:
        assert len(df.variables.keys()) == 1
        assert df["time"].size == 11


def test_open_mfdataset_data_vars_time():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex"],
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


def test_open_mfdataset_data_vars_sparse_time():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Particles_Particles_Per_Cell_proton"],
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


def test_open_mfdataset_data_vars_separate_times_single():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex"],
        separate_times=True,
    ) as df:
        coords = df.coords.sizes
        assert len(coords) == 2
        assert coords["time0"] == 11
        assert coords["X_Grid_mid"] == 16

        elec_x = "Electric_Field_Ex"
        elec_x_coords = df[elec_x].coords.sizes
        assert elec_x in df
        assert len(elec_x_coords) == 2
        assert "time0" in elec_x_coords
        assert "X_Grid_mid" in elec_x_coords

        assert elec_x_coords["time0"] == 11
        assert elec_x_coords["X_Grid_mid"] == 16


def test_open_mfdataset_data_vars_separate_times_multiple():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Electric_Field_Ey"],
        separate_times=True,
    ) as df:
        coords = df.coords.sizes
        assert len(coords) == 2
        assert coords["time0"] == 11
        assert coords["X_Grid_mid"] == 16

        elec_x = "Electric_Field_Ex"
        elec_x_coords = df[elec_x].coords.sizes
        assert elec_x in df
        assert len(elec_x_coords) == 2
        assert "time0" in elec_x_coords
        assert "X_Grid_mid" in elec_x_coords

        assert elec_x_coords["time0"] == 11
        assert elec_x_coords["X_Grid_mid"] == 16

        elec_y = "Electric_Field_Ey"
        elec_y_coords = df[elec_y].coords.sizes
        assert elec_y in df
        assert len(elec_y_coords) == 2
        assert "time0" in elec_y_coords
        assert "X_Grid_mid" in elec_y_coords

        assert elec_y_coords["time0"] == 11
        assert elec_y_coords["X_Grid_mid"] == 16


def test_open_mfdataset_data_vars_separate_times_multiple_times_keep_particles():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Particles_Px_electron_beam"],
        separate_times=True,
        keep_particles=True,
    ) as df:
        coords = df.coords.sizes
        assert len(coords) == 5
        assert coords["time0"] == 11
        assert coords["time1"] == 1
        assert coords["time2"] == 1
        assert coords["X_Grid_mid"] == 16
        assert coords["ID_electron_beam"] == 1440

        elec_x = "Electric_Field_Ex"
        elec_x_coords = df[elec_x].coords.sizes
        assert elec_x in df
        assert len(elec_x_coords) == 2
        assert "time0" in elec_x_coords
        assert "X_Grid_mid" in elec_x_coords

        assert elec_x_coords["time0"] == 11
        assert elec_x_coords["X_Grid_mid"] == 16

        particle_px = "Particles_Px_electron_beam"
        particle_px_coords = df[particle_px].coords.sizes
        assert particle_px in df
        assert len(particle_px_coords) == 2
        assert "time2" in particle_px_coords
        assert "ID_electron_beam" in particle_px_coords

        assert particle_px_coords["time2"] == 1
        assert particle_px_coords["ID_electron_beam"] == 1440


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_open_dataset_deck_path_default(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf") as df:
        assert "deck" in df.attrs


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_open_dataset_deck_path_failed(xrlib: XRLibrary):
    with pytest.raises(FileNotFoundError):
        xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf", deck_path="non_existent.deck")


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_open_dataset_deck_path_relative(xrlib: XRLibrary):
    with xrlib.open_dataset(TEST_FILES_DIR / "0000.sdf", deck_path="input.deck") as df:
        assert "deck" in df.attrs
        assert "constant" in df.attrs["deck"]


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_open_dataset_deck_path_absolute(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf", deck_path=TEST_FILES_DIR / "input.deck"
    ) as df:
        assert "deck" in df.attrs
        assert "constant" in df.attrs["deck"]


@pytest.mark.parametrize("xrlib", [xr, sdfxr])
def test_open_dataset_deck_path_absolute_other_path(xrlib: XRLibrary):
    with xrlib.open_dataset(
        TEST_FILES_DIR / "0000.sdf", deck_path=TEST_3D_DIST_FN / "input.deck"
    ) as df:
        assert "deck" in df.attrs
        assert "constant" not in df.attrs["deck"]


def test_open_mfdataset_deck_path_default():
    with sdfxr.open_mfdataset(TEST_FILES_DIR.glob("*.sdf")) as df:
        assert "deck" in df.attrs


def test_open_mfdataset_deck_path_failed():
    with pytest.raises(FileNotFoundError):
        sdfxr.open_mfdataset(
            TEST_FILES_DIR.glob("*.sdf"), deck_path="non_existent.deck"
        )


def test_open_mfdataset_deck_path_relative():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"),
        deck_path="input.deck",
    ) as df:
        assert "deck" in df.attrs
        assert "constant" in df.attrs["deck"]


def test_open_mfdataset_deck_path_absolute():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"), deck_path=TEST_FILES_DIR / "input.deck"
    ) as df:
        assert "deck" in df.attrs
        assert "constant" in df.attrs["deck"]


def test_open_mfdataset_deck_path_absolute_other_path():
    with sdfxr.open_mfdataset(
        TEST_FILES_DIR.glob("*.sdf"), deck_path=TEST_3D_DIST_FN / "input.deck"
    ) as df:
        assert "deck" in df.attrs
        assert "constant" not in df.attrs["deck"]
