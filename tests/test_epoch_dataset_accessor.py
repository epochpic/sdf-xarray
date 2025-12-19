import tempfile
from importlib.metadata import version

import matplotlib as mpl
import numpy as np
import pytest
import xarray as xr
from matplotlib.animation import PillowWriter
from packaging.version import Version

from sdf_xarray import download, open_mfdataset

mpl.use("Agg")

# TODO Remove this once the new kwarg options are fully implemented
if Version(version("xarray")) >= Version("2025.8.0"):
    xr.set_options(use_new_combine_kwarg_defaults=True)

TEST_FILES_DIR_1D = download.fetch_dataset("test_files_1D")
TEST_FILES_DIR_2D = download.fetch_dataset("test_two_probes_2D")
TEST_FILES_DIR_2D_MW = download.fetch_dataset("test_files_2D_moving_window")
TEST_FILES_DIR_3D = download.fetch_dataset("test_files_3D")


def test_rescale_coords_X():
    multiplier = 1e3
    unit_label = "mm"

    with xr.open_dataset(TEST_FILES_DIR_3D / "0000.sdf") as ds:
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

    with xr.open_dataset(TEST_FILES_DIR_3D / "0000.sdf") as ds:
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

    with xr.open_dataset(TEST_FILES_DIR_3D / "0000.sdf") as ds:
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

    with xr.open_dataset(TEST_FILES_DIR_3D / "0000.sdf") as ds:
        ds_rescaled = ds.epoch.rescale_coords(
            multiplier=multiplier,
            unit_label=unit_label,
            coord_names=["X_Grid_mid"],
        )

        assert ds_rescaled["X_Grid_mid"].attrs["units"] == unit_label
        assert ds_rescaled["X_Grid_mid"].attrs["long_name"] == "X"
        assert ds_rescaled["X_Grid_mid"].attrs["full_name"] == "Grid/Grid_mid"


def test_rescale_coords_non_existent_coord():
    with xr.open_dataset(TEST_FILES_DIR_3D / "0000.sdf") as ds:
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

    with open_mfdataset(TEST_FILES_DIR_3D.glob("*.sdf")) as ds:
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


def test_animate_multiple_accessor():
    with open_mfdataset(TEST_FILES_DIR_1D.glob("*.sdf")) as ds:
        assert hasattr(ds, "epoch")
        assert hasattr(ds.epoch, "animate_multiple")


def test_animate_multiple_headless_single():
    with open_mfdataset(TEST_FILES_DIR_1D.glob("*.sdf")) as ds:
        anim = ds.epoch.animate_multiple(ds["Derived_Number_Density_electron"])

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_animate_multiple_headless_multiple():
    with open_mfdataset(TEST_FILES_DIR_1D.glob("*.sdf")) as ds:
        anim = ds.epoch.animate_multiple(
            ds["Derived_Number_Density_electron"], ds["Derived_Number_Density_proton"]
        )

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_animate_multiple_headless_single_kwargs():
    with open_mfdataset(TEST_FILES_DIR_2D.glob("*.sdf")) as ds:
        anim = ds.epoch.animate_multiple(
            ds["Derived_Number_Density_Electron"], datasets_kwargs=[{"cmap": "viridis"}]
        )
        # Force the first frame to be drawn
        anim._func(0)
        ax = anim._fig.axes[0]

        mesh = next((m for m in ax.get_children() if hasattr(m, "get_cmap")), None)
        assert mesh is not None, "No artist with a colormap found"
        assert mesh.get_cmap().name == "viridis"

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_animate_multiple_headless_multiple_kwargs():
    with open_mfdataset(TEST_FILES_DIR_2D.glob("*.sdf")) as ds:
        anim = ds.epoch.animate_multiple(
            ds["Derived_Number_Density_Electron"],
            ds["Derived_Number_Density_Ion_H"],
            datasets_kwargs=[{"cmap": "viridis"}, {"cmap": "plasma"}],
        )
        # Force the first frame to be drawn
        anim._func(0)
        ax = anim._fig.axes[0]

        # Collect all artists that have a colormap
        meshes = [m for m in ax.get_children() if hasattr(m, "get_cmap")]
        assert len(meshes) == 2, "Expected two artists with colormaps"

        # Check colormaps in order
        expected_cm = ["viridis", "plasma"]
        for mesh, expected in zip(meshes, expected_cm):
            assert mesh.get_cmap().name == expected

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")
