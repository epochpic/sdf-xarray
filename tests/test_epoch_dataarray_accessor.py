import pathlib
import tempfile
from importlib.metadata import version

import matplotlib as mpl
import numpy as np
import pytest
import xarray as xr
from matplotlib.animation import PillowWriter
from packaging.version import Version

import sdf_xarray.plotting as sxp
from sdf_xarray import SDFPreprocess, open_mfdataset

mpl.use("Agg")

# TODO Remove this once the new kwarg options are fully implemented
if Version(version("xarray")) >= Version("2025.8.0"):
    xr.set_options(use_new_combine_kwarg_defaults=True)

EXAMPLE_FILES_DIR_1D = pathlib.Path(__file__).parent / "example_files_1D"
EXAMPLE_FILES_DIR_2D_MW = (
    pathlib.Path(__file__).parent / "example_files_2D_moving_window"
)


def test_animation_accessor():
    array = xr.DataArray(
        [1, 2, 3],
        dims=["x"],
        coords={"x": [0, 1, 2]},
        attrs={"long_name": "Test Array", "units": "m"},
    )
    assert hasattr(array, "epoch")
    assert hasattr(array.epoch, "animate")


def test_animate_headless():
    with open_mfdataset(EXAMPLE_FILES_DIR_1D.glob("*.sdf")) as ds:
        anim = ds["Derived_Number_Density_electron"].epoch.animate()

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_xr_animate_headless():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        anim = ds["Derived_Number_Density_electron"].epoch.animate()

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_xr_get_frame_title_no_optional_params():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "time = 5.47e-14 [s]"
        result = sxp.get_frame_title(data, 0)
        assert expected_result == result


def test_xr_get_frame_title_sdf_name():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "time = 5.47e-14 [s], 0000.sdf"
        result = sxp.get_frame_title(data, 0, display_sdf_name=True)
        assert expected_result == result


def test_xr_get_frame_title_custom_title():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Test Title, time = 5.47e-14 [s]"
        result = sxp.get_frame_title(data, 0, title_custom="Test Title")
        assert expected_result == result


def test_xr_get_frame_title_custom_title_and_sdf_name():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Test Title, time = 5.47e-14 [s], 0000.sdf"
        result = sxp.get_frame_title(
            data, 0, display_sdf_name=True, title_custom="Test Title"
        )
        assert expected_result == result


def test_xr_calculate_window_boundaries_1D():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        data = ds["Derived_Number_Density_electron"][:, :, 50]
        expected_result = np.array(
            [[0, 1], [0.49, 1.49], [0.99, 1.99], [1.49, 2.49], [1.99, 2.99]]
        )
        result = sxp.calculate_window_boundaries(data)
        assert result == pytest.approx(expected_result, abs=0.1)


def test_xr_calculate_window_boundaries_2D():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = np.array(
            [[0, 1], [0.49, 1.49], [0.99, 1.99], [1.49, 2.49], [1.99, 2.99]]
        )
        result = sxp.calculate_window_boundaries(data)
        assert result == pytest.approx(expected_result, abs=0.1)


def test_xr_calculate_window_boundaries_1D_xlim():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        data = ds["Derived_Number_Density_electron"][:, :, 50]
        expected_result = np.array(
            [[0.1, 0.9], [0.59, 1.39], [1.09, 1.89], [1.59, 2.39], [2.09, 2.89]]
        )
        result = sxp.calculate_window_boundaries(data, xlim=(0.1, 0.9))
        assert result == pytest.approx(expected_result, abs=0.1)


def test_xr_calculate_window_boundaries_2D_xlim():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = np.array(
            [[0.1, 0.9], [0.59, 1.39], [1.09, 1.89], [1.59, 2.39], [2.09, 2.89]]
        )
        result = sxp.calculate_window_boundaries(data, xlim=(0.1, 0.9))
        assert result == pytest.approx(expected_result, abs=0.1)


def test_xr_compute_global_limits():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        result_min, result_max = sxp.compute_global_limits(
            ds["Derived_Number_Density_electron"]
        )
        expected_result_min = 8.07e19
        expected_result_max = 1.17e20
        assert result_min == pytest.approx(expected_result_min, abs=1e18)
        assert result_max == pytest.approx(expected_result_max, abs=1e19)


def test_xr_compute_global_limits_percentile():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        result_min, result_max = sxp.compute_global_limits(
            ds["Derived_Number_Density_electron"], 40, 45
        )
        expected_result_min = 9.84e19
        expected_result_max = 9.94e19
        assert result_min == pytest.approx(expected_result_min, abs=1e18)
        assert result_max == pytest.approx(expected_result_max, abs=1e18)


def test_xr_compute_global_limits_NaNs():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        result_min, result_max = sxp.compute_global_limits(
            ds["Derived_Number_Density_electron"]
        )
        expected_result_min = 5.51e-1
        expected_result_max = 2.70
        assert result_min == pytest.approx(expected_result_min, abs=1e-2)
        assert result_max == pytest.approx(expected_result_max, abs=1e-1)
