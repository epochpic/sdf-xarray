import tempfile
from importlib.metadata import version

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr
from matplotlib.animation import PillowWriter
from matplotlib.colors import ListedColormap
from matplotlib.container import BarContainer
from mpl_toolkits.mplot3d import Axes3D
from packaging.version import Version

import sdf_xarray as sdfxr
import sdf_xarray.plotting as sxp
from sdf_xarray import SDFPreprocess, download

mpl.use("Agg")

# TODO Remove this once the new kwarg options are fully implemented
if Version(version("xarray")) >= Version("2025.8.0"):
    xr.set_options(use_new_combine_kwarg_defaults=True)

TEST_FILES_DIR_1D = download.fetch_dataset("test_files_1D")
TEST_FILES_DIR_2D_MW = download.fetch_dataset("test_files_2D_moving_window")
TEST_FILES_DIR_3D = download.fetch_dataset("test_files_3D")


@pytest.fixture
def subplots():
    fig, ax = plt.subplots()
    yield (fig, ax)
    plt.close(fig)


def test_animation_accessor():
    array = xr.DataArray(
        [1, 2, 3],
        dims=["x"],
        coords={"x": [0, 1, 2]},
        attrs={"long_name": "Test Array", "units": "m"},
    )
    assert hasattr(array, "epoch")
    assert hasattr(array.epoch, "animate")


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
def test_animate_headless(xrlib, params):
    with xrlib.open_mfdataset(TEST_FILES_DIR_1D.glob("*.sdf"), **params) as ds:
        anim = ds["Derived_Number_Density_electron"].epoch.animate()

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")


def test_get_frame_title_no_optional_params():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Time = 5.47e-14 [s]"
        result = sxp.get_frame_title(data, 0)
        assert expected_result == result


def test_get_frame_title_sdf_name():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Time = 5.47e-14 [s], 0000.sdf"
        result = sxp.get_frame_title(data, 0, display_sdf_name=True)
        assert expected_result == result


def test_get_frame_title_custom_title():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Test Title, Time = 5.47e-14 [s]"
        result = sxp.get_frame_title(data, 0, title_custom="Test Title")
        assert expected_result == result


def test_get_frame_title_custom_title_and_sdf_name():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        data = ds["Derived_Number_Density_electron"]
        expected_result = "Test Title, Time = 5.47e-14 [s], 0000.sdf"
        result = sxp.get_frame_title(
            data, 0, display_sdf_name=True, title_custom="Test Title"
        )
        assert expected_result == result


def test_get_frame_title_Z_Grid_mid():
    with xr.open_dataset(TEST_FILES_DIR_3D / "0001.sdf") as ds:
        data = ds["Derived_Number_Density_Electron"]
        expected_result = "Z = 3.91e-07 [m]"
        result = sxp.get_frame_title(data, 0, t="Z_Grid_mid")
        assert expected_result == result


def test_calculate_window_boundaries_1D():
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
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


def test_calculate_window_boundaries_2D():
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
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


def test_calculate_window_boundaries_1D_xlim():
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
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


def test_calculate_window_boundaries_2D_xlim():
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
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


def test_compute_global_limits():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
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


def test_compute_global_limits_percentile():
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
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


def test_compute_global_limits_NaNs():
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
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


def test_epoch_plot_simple_1d_dataset(subplots):
    with xr.open_mfdataset(
        TEST_FILES_DIR_1D.glob("*.sdf"),
        compat="no_conflicts",
        join="outer",
        preprocess=SDFPreprocess(),
    ) as ds:
        _, ax = subplots
        ds["Derived_Number_Density_electron"].isel(time=0).epoch.plot(ax=ax)

        assert len(ax.lines) == 1
        assert ax.get_xlabel() == "X [m]"


def test_epoch_plot_simple_2d_dataset(subplots):
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        _, ax = subplots
        ds["Derived_Number_Density_electron"].isel(time=0).epoch.plot(ax=ax)

        assert len(ax.collections) > 0
        assert ax.get_xlabel() == "X [m]"
        assert ax.get_ylabel() == "Y [m]"


def test_epoch_plot_simple_3d_dataset_slice(subplots):
    with xr.open_dataset(TEST_FILES_DIR_3D / "0001.sdf") as ds:
        _, ax = subplots
        ds["Derived_Number_Density_Electron"].isel(Z_Grid_mid=0).epoch.plot(ax=ax)

        assert len(ax.collections) > 0
        assert ax.get_xlabel() == "X [m]"
        assert ax.get_ylabel() == "Y [m]"


def test_epoch_plot_flips_axis_order_for_2d_data(subplots):
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        _, ax = subplots
        ds["Derived_Number_Density_electron"].isel(time=0).epoch.plot(ax=ax)

        assert ax.get_xlabel() == "X [m]"
        assert ax.get_ylabel() == "Y [m]"


def test_epoch_plot_flips_axis_order_for_2d_data_with_additional_params(subplots):
    with xr.open_mfdataset(
        TEST_FILES_DIR_2D_MW.glob("*.sdf"),
        preprocess=SDFPreprocess(),
        combine="nested",
        compat="no_conflicts",
        join="outer",
    ) as ds:
        _, ax = subplots
        ds["Derived_Number_Density_electron"].isel(time=0).epoch.plot(
            ax=ax,
            xlim=(0.5, 1.0),
            ylim=(0.0, 0.5),
        )

        assert ax.get_xlabel() == "X [m]"
        assert ax.get_ylabel() == "Y [m]"
        assert ax.get_xlim() == pytest.approx((0.5, 1.0), abs=1e-2)
        assert ax.get_ylim() == pytest.approx((0.0, 0.5), abs=1e-2)


def _make_3d_da(shape=(4, 5, 6)):
    """Small synthetic 3-D DataArray with the metadata voxel_plot expects."""
    nx, ny, nz = shape
    rng = np.random.default_rng(42)
    data = rng.uniform(0.0, 1.0, (nx, ny, nz)).astype(np.float64)
    return xr.DataArray(
        data,
        dims=["X_Grid_mid", "Y_Grid_mid", "Z_Grid_mid"],
        coords={
            "X_Grid_mid": xr.Variable(
                "X_Grid_mid",
                np.linspace(0.0, 1e-5, nx),
                attrs={"long_name": "X", "units": "m"},
            ),
            "Y_Grid_mid": xr.Variable(
                "Y_Grid_mid",
                np.linspace(0.0, 2e-5, ny),
                attrs={"long_name": "Y", "units": "m"},
            ),
            "Z_Grid_mid": xr.Variable(
                "Z_Grid_mid",
                np.linspace(0.0, 3e-5, nz),
                attrs={"long_name": "Z", "units": "m"},
            ),
        },
        attrs={"long_name": "Test Density", "units": "1/m^3"},
    )


@pytest.fixture
def close_figs():
    yield
    plt.close("all")


def test_recover_vertex_coord_size():
    mid = xr.DataArray(np.linspace(0.5, 4.5, 5))
    vertex = sxp._recover_vertex_coord(mid)
    assert vertex.size == mid.size + 1


def test_recover_vertex_coord_values():
    mid = xr.DataArray(np.array([0.5, 1.5, 2.5]))
    vertex = sxp._recover_vertex_coord(mid)
    np.testing.assert_allclose(vertex, [0.0, 1.0, 2.0, 3.0])


def test_shift_cmap_returns_listed_colormap():
    result = sxp.shift_cmap("RdBu", vmin=-1.0, vmax=1.0, vcenter=0.0)
    assert isinstance(result, ListedColormap)


def test_shift_cmap_total_colors():
    result = sxp.shift_cmap("RdBu", vmin=-1.0, vmax=1.0, vcenter=0.0, N=100)
    assert len(result.colors) == 100


def test_shift_cmap_asymmetric_center():
    result = sxp.shift_cmap("viridis", vmin=0.0, vmax=1.0, vcenter=0.25, N=200)
    assert isinstance(result, ListedColormap)
    assert len(result.colors) == 200


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_returns_fig_and_ax():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da)
    assert isinstance(ax, Axes3D)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_accepts_axes():
    da = _make_3d_da()
    _, ax = plt.subplots(figsize=(8, 6), subplot_kw={"projection": "3d"})
    sxp.voxel_plot(da, ax=ax)
    assert isinstance(ax, Axes3D)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_axis_labels():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da)
    assert ax.get_xlabel() == "X [m]"
    assert ax.get_ylabel() == "Y [m]"
    assert ax.get_zlabel() == "Z [m]"


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_default_axis_limits():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    zlim = ax.get_zlim()
    assert xlim[0] < xlim[1]
    assert ylim[0] < ylim[1]
    assert zlim[0] < zlim[1]


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_with_xlim_ylim_zlim():
    da = _make_3d_da()
    x0, x1 = 2e-6, 8e-6
    y0, y1 = 2e-6, 1.8e-5
    z0, z1 = 5e-6, 2.5e-5
    _, ax = sxp.voxel_plot(da, xlim=(x0, x1), ylim=(y0, y1), zlim=(z0, z1))
    assert ax.get_xlim() == pytest.approx((x0, x1), rel=0.1)
    assert ax.get_ylim() == pytest.approx((y0, y1), rel=0.1)
    assert ax.get_zlim() == pytest.approx((z0, z1), rel=0.1)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_with_explicit_vmin_vmax():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da, vmin=0.2, vmax=0.8)
    assert isinstance(ax, Axes3D)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_with_vcenter():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da, cmap="RdBu", vcenter=1e-2)
    assert isinstance(ax, Axes3D)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_with_custom_mask():
    da = _make_3d_da()
    mask = da.values > 0.5
    _, ax = sxp.voxel_plot(da, mask=mask)
    assert isinstance(ax, Axes3D)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_aspect_auto():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da, aspect="auto")
    box = ax.get_box_aspect()
    # voxel_plot uses vertex coords (half-cell beyond midpoints) for axis ranges;
    # matplotlib normalizes the absolute values, so only ratios are stable
    x_vert = sxp._recover_vertex_coord(da["X_Grid_mid"])
    y_vert = sxp._recover_vertex_coord(da["Y_Grid_mid"])
    z_vert = sxp._recover_vertex_coord(da["Z_Grid_mid"])
    x_range = x_vert.max() - x_vert.min()
    y_range = y_vert.max() - y_vert.min()
    z_range = z_vert.max() - z_vert.min()
    assert box[1] / box[0] == pytest.approx(y_range / x_range, rel=0.05)
    assert box[2] / box[0] == pytest.approx(z_range / x_range, rel=0.05)


@pytest.mark.usefixtures("close_figs")
def test_voxel_plot_aspect_custom_tuple():
    da = _make_3d_da()
    _, ax = sxp.voxel_plot(da, aspect=(1.0, 2.0, 3.0))
    box = ax.get_box_aspect()
    assert box[1] / box[0] == pytest.approx(2.0, rel=0.01)
    assert box[2] / box[0] == pytest.approx(3.0, rel=0.01)


@pytest.mark.usefixtures("close_figs")
def test_epoch_plot_dispatches_to_voxel_for_3d_spatial_data():
    with xr.open_dataset(TEST_FILES_DIR_3D / "0001.sdf") as ds:
        da = ds["Derived_Number_Density_Electron"].isel(
            X_Grid_mid=slice(0, 4),
            Y_Grid_mid=slice(0, 4),
            Z_Grid_mid=slice(0, 4),
        )
        _, ax = da.epoch.plot()
        assert isinstance(ax, Axes3D)
        assert ax.get_xlabel() == "X [m]"
        assert ax.get_ylabel() == "Y [m]"
        assert ax.get_zlabel() == "Z [m]"


def test_resize_basic():
    da = _make_3d_da(shape=(8, 10, 12))
    da_small = da.epoch.resize((4, 5, 6))
    assert da_small.shape == (4, 5, 6)
    assert da_small.dims == da.dims


def test_resize_stores_original_shape_attrs():
    da = _make_3d_da(shape=(8, 10, 12))
    da_small = da.epoch.resize((4, 5, 6))
    assert da_small.attrs["original_shape"] == (8, 10, 12)


def test_resize_coord_range_preserved():
    da = _make_3d_da(shape=(8, 10, 12))
    da_small = da.epoch.resize((4, 5, 6))
    # For _mid coords, resize preserves the vertex (cell-edge) range rather than
    # the midpoint values; check that the outer vertices are unchanged
    orig_vertex = sxp._recover_vertex_coord(da["X_Grid_mid"])
    new_vertex = sxp._recover_vertex_coord(da_small["X_Grid_mid"])
    np.testing.assert_allclose(float(new_vertex[0]), float(orig_vertex[0]), rtol=1e-6)
    np.testing.assert_allclose(float(new_vertex[-1]), float(orig_vertex[-1]), rtol=1e-6)


def test_resize_wrong_ndim_raises():
    da = _make_3d_da()
    with pytest.raises(ValueError, match="dimensions"):
        da.epoch.resize((4, 5))


def test_resize_with_mid_coord():
    da = _make_3d_da(shape=(6, 8, 10))
    da_small = da.epoch.resize((3, 4, 5))
    assert da_small.shape == (3, 4, 5)
    for dim in da_small.dims:
        assert da_small[dim].size == da_small.sizes[dim]


def test_limit_reduces_coord_range():
    da = _make_3d_da()
    x_mid = 5e-6
    da_lim = da.epoch.limit(((0.0, x_mid), (None, None), (None, None)))
    assert float(da_lim["X_Grid_mid"][-1]) <= x_mid + 1e-7


def test_limit_with_none_uses_existing_bounds():
    da = _make_3d_da()
    da_lim = da.epoch.limit(((None, None), (None, None), (None, None)))
    assert da_lim.shape == da.shape


def test_limit_stores_original_lims_on_coord():
    da = _make_3d_da()
    x_min = float(da["X_Grid_mid"][0])
    x_max = float(da["X_Grid_mid"][-1])
    da_lim = da.epoch.limit(((0.0, 5e-6), (None, None), (None, None)))
    assert da_lim["X_Grid_mid"].attrs["original_lims"] == pytest.approx(
        (x_min, x_max), rel=1e-6
    )


def test_limit_no_drop():
    da = _make_3d_da()
    da_lim = da.epoch.limit(((0.0, 5e-6), (None, None), (None, None)), drop=False)
    assert da_lim.shape == da.shape
    assert np.any(np.isnan(da_lim.values))


def test_animate_raises_for_4d_data():
    da = xr.DataArray(
        np.zeros((3, 4, 5, 6)),
        dims=["time", "X_Grid_mid", "Y_Grid_mid", "Z_Grid_mid"],
        coords={
            "time": xr.Variable(
                "time", [1.0, 2.0, 3.0], attrs={"long_name": "Time", "units": "s"}
            )
        },
    )
    with pytest.raises(NotImplementedError, match="Voxel animations"):
        da.epoch.animate()
