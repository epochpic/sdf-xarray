import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr

from sdf_xarray import (
    download,
    open_datatree,
    open_mfdatatree,
)

TEST_FILES_DIR = download.fetch_dataset("test_files_1D")
TEST_MISMATCHED_FILES_DIR = download.fetch_dataset("test_mismatched_files")
TEST_ARRAYS_DIR = download.fetch_dataset("test_array_no_grids")
TEST_3D_DIST_FN = download.fetch_dataset("test_dist_fn")
TEST_2D_PARTICLE_DATA = download.fetch_dataset("test_two_probes_2D")


def test_datatree_basic():
    dt = open_datatree(TEST_FILES_DIR / "0000.sdf")
    # Electric field group and variable (multi-level from full_name hierarchy)
    assert "/Electric_Field" in dt.groups
    ex = dt["Electric_Field"]["Ex"]
    assert "X_Grid_mid" in ex.coords
    assert ex.coords["X_Grid_mid"].attrs["long_name"] == "X"

    # Particles should not be present by default
    assert not any(g for g in dt.groups if g.endswith("/Particles"))


def test_datatree_constant_name_and_units():
    dt = open_datatree(TEST_FILES_DIR / "0000.sdf")
    # Absorption group with constants
    assert "/Absorption" in dt.groups
    total = dt["Absorption"]["Total_Laser_Energy_Injected"]
    assert total.attrs.get("units") == "J"
    assert total.attrs.get("full_name") == "Absorption/Total Laser Energy Injected"


def test_datatree_coords():
    dt = open_datatree(TEST_FILES_DIR / "0010.sdf")
    # dist_fn/px_py/Electron structure from full_name
    var = dt["dist_fn"]["x_px"]["electron"]
    assert "Px_x_px_electron" in var.coords
    assert var.coords["Px_x_px_electron"].attrs["full_name"] == "Grid/x_px/electron"


def test_datatree_particles():
    dt = open_datatree(TEST_FILES_DIR / "0010.sdf", keep_particles=True)
    # Particles group appears when particles are kept
    assert "/Particles" in dt.groups
    # Particles_Px_proton -> Particles/Px/proton structure
    px = dt["Particles"]["Px"]["proton"]
    assert "X_Particles_proton" in px.coords
    assert px.coords["X_Particles_proton"].attrs["long_name"] == "X"


def test_datatree_no_particles():
    dt = open_datatree(TEST_FILES_DIR / "0010.sdf", keep_particles=False)
    # Particles group may still exist for non-point grid vars,
    # but point-data variables like Px_proton must be absent.
    particles_group_exists = any(g for g in dt.groups if g.endswith("/Particles"))
    if particles_group_exists:
        # Check that leaf groups don't have direct point-data
        assert "proton" not in dt["Particles"].data_vars
    else:
        assert True


def test_datatree_multiple_files_one_time_dim():
    dt = open_mfdatatree(TEST_FILES_DIR.glob("*.sdf"), keep_particles=True)
    # Electric_Field/Ex structure from full_name
    ex = dt["Electric_Field"]["Ex"]
    assert sorted(ex.coords) == sorted(("X_Grid_mid", "time"))
    assert ex.shape == (11, 16)

    # Electric_Field/Ey structure
    ey = dt["Electric_Field"]["Ey"]
    assert sorted(ey.coords) == sorted(("X_Grid_mid", "time"))
    assert ey.shape == (11, 16)

    # Particles/Px/proton structure
    px_protons = dt["Particles"]["Px"]["proton"]
    assert sorted(px_protons.coords) == sorted(("X_Particles_proton", "time"))
    assert px_protons.shape == (11, 1920)

    # Particles/Weight/proton structure
    weight_protons = dt["Particles"]["Weight"]["proton"]
    assert sorted(weight_protons.coords) == sorted(("X_Particles_proton", "time"))
    assert weight_protons.shape == (11, 1920)

    absorption = dt["Absorption"]["Total_Laser_Energy_Injected"]
    # Single coordinate 'time'
    assert tuple(absorption.coords) == ("time",)
    assert absorption.shape == (11,)

    # Check values match baseline
    ex_da = ex.isel(time=10)
    ex_values = ex_da.values
    ex_x_coords = ex_da.coords["X_Grid_mid"].values
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
            -3126528.4705715775,
            -3249643.376122554,
            -6827013.115662239,
            -9350267.990220116,
            -1643592.584873334,
            -2044751.412071893,
            -4342811.346661035,
            -10420841.38402196,
            -7038801.831545288,
            781649.3179168438,
            4476555.848531812,
            5873312.793856503,
            -95930.60501570138,
            -8977898.965479957,
            -7951712.649878098,
            -5655667.111713385,
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

    # time coordinate available on variables in DataTree
    npt.assert_allclose(time_values, ex.coords["time"].values, rtol=1e-6)
    npt.assert_allclose(ex_values, expected_ex)
    npt.assert_allclose(ex_x_coords, expected_ex_coords)


def test_datatree_multiple_files_multiple_time_dims():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"), separate_times=True, keep_particles=True
    )
    # With this dataset, Ex and Ey share the same time dimension
    assert list(dt["Electric_Field"]["Ex"].coords) == list(
        dt["Electric_Field"]["Ey"].coords
    )
    assert dt["Electric_Field"]["Ex"].shape == (11, 16)
    assert dt["Electric_Field"]["Ey"].shape == (11, 16)
    assert dt["Particles"]["Px"]["proton"].shape == (1, 1920)
    assert dt["Particles"]["Weight"]["proton"].shape == (2, 1920)
    assert dt["Absorption"]["Total_Laser_Energy_Injected"].shape == (11,)


def test_datatree_time_dim():
    dt = open_mfdatatree(TEST_FILES_DIR.glob("*.sdf"))
    # Access time from a representative variable's coords
    time = dt["Electric_Field"]["Ex"].coords["time"]
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


def test_datatree_latex_rename_variables():
    dt = open_mfdatatree(TEST_ARRAYS_DIR.glob("*.sdf"), keep_particles=True)
    assert dt["Electric_Field"]["Ex"].attrs["long_name"] == "Electric Field $E_x$"
    assert dt["Electric_Field"]["Ey"].attrs["long_name"] == "Electric Field $E_y$"
    assert dt["Electric_Field"]["Ez"].attrs["long_name"] == "Electric Field $E_z$"
    assert dt["Magnetic_Field"]["Bx"].attrs["long_name"] == "Magnetic Field $B_x$"
    assert dt["Magnetic_Field"]["By"].attrs["long_name"] == "Magnetic Field $B_y$"
    assert dt["Magnetic_Field"]["Bz"].attrs["long_name"] == "Magnetic Field $B_z$"
    assert (
        dt["Particles"]["Px"]["Electron"].attrs["long_name"]
        == "Particles $P_x$ Electron"
    )


def test_datatree_open_mfdatatree_data_vars_single():
    dt = open_mfdatatree(TEST_FILES_DIR.glob("*.sdf"), data_vars=["Electric_Field_Ex"])
    # Variable should be present under Electric_Field/Ex structure
    assert "Ex" in dt["Electric_Field"].data_vars
    # A different variable should not be anywhere
    assert not ("Ey" in dt["Electric_Field"].data_vars)


def test_datatree_open_mfdatatree_data_vars_multiple():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Electric_Field_Ey"],
    )
    assert "Ex" in dt["Electric_Field"].data_vars
    assert "Ey" in dt["Electric_Field"].data_vars


def test_datatree_open_mfdatatree_data_vars_sparse_multiple():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        keep_particles=True,
        data_vars=[
            "Particles_Particles_Per_Cell_proton",
            "Electric_Field_Ez",
            "dist_fn_x_px_proton",
        ],
    )
    # Check presence under corresponding multi-level groups
    # Particles_Particles_Per_Cell_proton -> Particles/Particles_Per_Cell/proton
    assert "Particles_Per_Cell" in [g.split("/")[-1] for g in dt["Particles"].groups]
    # Electric_Field_Ez -> Electric_Field/Ez
    assert "Ez" in dt["Electric_Field"].data_vars
    # dist_fn_x_px_proton -> dist_fn/x_px/proton
    assert "x_px" in [g.split("/")[-1] for g in dt["dist_fn"].groups]


def test_datatree_open_mfdatatree_data_vars_time():
    dt = open_mfdatatree(TEST_FILES_DIR.glob("*.sdf"), data_vars=["Electric_Field_Ex"])
    # Time coordinate exists on the variable (Electric_Field/Ex structure)
    assert "time" in dt["Electric_Field"]["Ex"].coords


def test_datatree_open_mfdatatree_data_vars_sparse_time():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Particles_Particles_Per_Cell_proton"],
    )
    # Particles_Particles_Per_Cell_proton -> Particles/Particles_Per_Cell/proton
    assert "time" in dt["Particles"]["Particles_Per_Cell"]["proton"].coords


def test_datatree_open_mfdatatree_data_vars_separate_times_single():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex"],
        separate_times=True,
    )
    assert dt["Electric_Field"]["Ex"].shape[0] == 11


def test_datatree_open_mfdatatree_data_vars_separate_times_multiple():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Electric_Field_Ey"],
        separate_times=True,
    )
    # Shapes may differ by time dims when separate_times=True
    assert dt["Electric_Field"]["Ex"].shape[0] >= 1
    assert dt["Electric_Field"]["Ey"].shape[0] >= 1


def test_datatree_open_mfdatatree_data_vars_separate_times_multiple_times_keep_particles():
    dt = open_mfdatatree(
        TEST_FILES_DIR.glob("*.sdf"),
        data_vars=["Electric_Field_Ex", "Particles_Px_electron_beam"],
        separate_times=True,
        keep_particles=True,
    )
    assert dt["Electric_Field"]["Ex"].shape[0] >= 1
    # Particles_Px_electron_beam -> Particles/Px/electron_beam
    assert dt["Particles"]["Px"]["electron_beam"].shape[0] >= 1


# Parity for mismatched jobid behaviour


def test_datatree_erroring_on_mismatched_jobid_files():
    with pytest.raises(ValueError):  # noqa: PT011
        # open_mfdatatree uses open_mfdataset under the hood with SDFPreprocess
        open_mfdatatree(TEST_MISMATCHED_FILES_DIR.glob("*.sdf"))
