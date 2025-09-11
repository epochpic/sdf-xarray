from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation


def get_frame_title(
    data: xr.DataArray,
    frame: int,
    display_sdf_name: bool = False,
    title_custom: str | None = None,
) -> str:
    """Generate the title for a frame"""
    # Adds custom text to the start of the title, if specified
    title_custom = "" if title_custom is None else f"{title_custom}, "
    # Adds the time and associated units to the title
    time = data["time"][frame].to_numpy()

    time_units = data["time"].attrs.get("units", False)
    time_units_formatted = f" [{time_units}]" if time_units else ""
    title_time = f"time = {time:.2e}{time_units_formatted}"

    # Adds sdf name to the title, if specifed
    title_sdf = f", {frame:04d}.sdf" if display_sdf_name else ""
    return f"{title_custom}{title_time}{title_sdf}"


def calculate_window_boundaries(
    data: xr.DataArray, xlim: tuple[float, float] | False = False
) -> np.ndarray:
    """Calculate the bounderies a moving window frame. If the user specifies xlim, this will
    be used as the initial bounderies and the window will move along acordingly.
    """
    x_grid = data["X_Grid_mid"].values
    x_half_cell = (x_grid[1] - x_grid[0]) / 2
    N_frames = data["time"].size

    # Find the window bounderies by finding the first and last non-NaN values in the 0th lineout
    # along the x-axis.
    window_boundaries = np.zeros((N_frames, 2))
    for i in range(N_frames):
        # Check if data is 1D
        if data.ndim == 2:
            target_lineout = data[i].values
        # Check if data is 2D
        if data.ndim == 3:
            target_lineout = data[i, :, 0].values
        x_grid_non_nan = x_grid[~np.isnan(target_lineout)]
        window_boundaries[i, 0] = x_grid_non_nan[0] - x_half_cell
        window_boundaries[i, 1] = x_grid_non_nan[-1] + x_half_cell

    # User's choice for initial window edge supercides the one calculated
    if xlim:
        window_boundaries = window_boundaries + xlim - window_boundaries[0]
    return window_boundaries


def compute_global_limits(
    data: xr.DataArray,
    min_percentile: float = 0,
    max_percentile: float = 100,
) -> tuple[float, float]:
    """Remove all NaN values from the target data to calculate the global minimum and maximum of the data.
    User defined percentiles can remove extreme outliers.
    """

    # Removes NaN values, needed for moving windows
    values_no_nan = data.values[~np.isnan(data.values)]

    # Finds the global minimum and maximum of the plot, based on the percentile of the data
    global_min = np.percentile(values_no_nan, min_percentile)
    global_max = np.percentile(values_no_nan, max_percentile)
    return global_min, global_max


def animate(
    data: xr.DataArray,
    fps: float = 10,
    min_percentile: float = 0,
    max_percentile: float = 100,
    title: str | None = None,
    display_sdf_name: bool = False,
    ax: plt.Axes | None = None,
    *,
    # 新增：坐标缩放与标签
    xscale: float = 1.0,
    yscale: float = 1.0,
    xlabel: str | None = None,
    ylabel: str | None = None,
    # 新增：帧选择
    frames: "list[int] | range | None" = None,
    frame_step: int = 1,
    # 新增：是否跟随移动窗口（x 轴每帧更新）
    follow_window: bool = True,
    **kwargs,
) -> "FuncAnimation":
    """Generate an animation (patched)

    - Respects user-provided norm or vmin/vmax
    - Supports x/y unit scaling and axis labels
    - Updates x-limits per frame when domain/window moves
    - Supports frame skipping via `frames` or `frame_step`
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    kwargs_original = kwargs.copy()

    if ax is None:
        _, ax = plt.subplots()

    # --------- global limits (can be heavy if data is huge) ----------
    # 如有需要可改成基于采样帧的分位数来避免一次性拉全量
    N_frames = data.sizes["time"]
    global_min, global_max = compute_global_limits(data, min_percentile, max_percentile)

    # 选择帧序列
    if frames is None:
        frames = range(0, N_frames, frame_step)

    # 维度与坐标名
    x_name = kwargs.get("x", "X_Grid_mid")
    y_name = kwargs.get("y", "Y_Grid_mid")

    # ---------- prepare norm / vmin / vmax ----------
    user_norm = kwargs_original.get("norm", None)
    user_vmin = kwargs_original.get("vmin", None)
    user_vmax = kwargs_original.get("vmax", None)

    if data.ndim == 3:
        if user_norm is not None:
            kwargs["norm"] = user_norm
            kwargs.pop("vmin", None)
            kwargs.pop("vmax", None)
        elif (user_vmin is not None) or (user_vmax is not None):
            if user_vmin is None:
                kwargs["vmin"] = global_min
            if user_vmax is None:
                kwargs["vmax"] = global_max
            kwargs.pop("norm", None)
        else:
            kwargs["norm"] = plt.Normalize(vmin=global_min, vmax=global_max)

        # 2D 绘图不让 xarray 自动加色标，统一手动加
        kwargs["add_colorbar"] = False

    # 默认坐标参数（xarray 会按名字找坐标）
    kwargs.setdefault("x", x_name)
    kwargs.setdefault("y", y_name)

    # ---------- 初始化第一帧 ----------
    def get_frame_da(i: int) -> xr.DataArray:
        da = data.isel(time=i)
        # 坐标单位缩放（只改坐标，不复制数据）
        coords_update = {}
        if xscale != 1.0 and x_name in da.coords:
            coords_update[x_name] = da.coords[x_name] * xscale
        if yscale != 1.0 and y_name in da.coords and da.ndim == 3:
            coords_update[y_name] = da.coords[y_name] * yscale
        if coords_update:
            da = da.assign_coords(coords_update)
        return da

    first = get_frame_da(frames[0] if hasattr(frames, "__getitem__") else next(iter(frames)))

    # 1D/2D 分开初始化
    if data.ndim == 2:
        plot = first.plot(ax=ax, **kwargs)
        ax.set_ylim(global_min, global_max)
    else:
        plot = first.plot(ax=ax, **kwargs)

    # 标题 & 轴标签
    ax.set_title(get_frame_title(data, frames[0] if hasattr(frames, "__getitem__") else 0, display_sdf_name, title))
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None and data.ndim == 3:
        ax.set_ylabel(ylabel)

    # 手动加 colorbar（仅 2D）
    if (data.ndim == 3) and kwargs_original.get("add_colorbar", True):
        long_name = data.attrs.get("long_name")
        units = data.attrs.get("units")
        cbar_label = f"{long_name} [${units}$]" if (long_name or units) else None
        cbar = plt.colorbar(plot, ax=ax, label=cbar_label)
    else:
        cbar = None

    # 预计算移动窗口（如果数据用 NaN 指示窗口）
    move_window_nans = np.isnan(np.sum(data.values))
    if move_window_nans:
        window_boundaries = calculate_window_boundaries(data, kwargs_original.get("xlim", False))
    else:
        window_boundaries = None

    # ---------- 帧更新 ----------
    def update(frame):
        da = get_frame_da(frame)

        # x 轴范围：优先 NaN 窗口，其次直接用该帧坐标范围（follow_window）
        if data.ndim == 3 and follow_window:
            if window_boundaries is not None:
                ax.set_xlim(*window_boundaries[frame] * (xscale if xscale != 1.0 else 1.0))
            else:
                x = da.coords[x_name].values
                if x.ndim == 1:
                    dx = (x[1] - x[0]) if x.size > 1 else 0.0
                    ax.set_xlim(x[0] - dx/2, x[-1] + dx/2)

        # 重新绘图（不 clear 轴，避免把 colorbar 干掉）
        # xarray 的 plot 返回新 mappable，老的我们移除掉以免堆叠
        # （也可选择复用 pcolormesh，但这里保持与你现有实现风格一致）
        nonlocal plot
        for coll in getattr(plot, "collections", []):
            coll.remove()
        plot = da.plot(ax=ax, **kwargs)

        # 更新标题
        ax.set_title(get_frame_title(data, frame, display_sdf_name, title))

        # 1D 固定 y-limits
        if data.ndim == 2:
            ax.set_ylim(global_min, global_max)

        # 同步 colorbar 的 mappable（2D 情况）
        if cbar is not None and data.ndim == 3:
            cbar.update_normal(plot)

        return (plot,)

    return FuncAnimation(
        ax.get_figure(),
        update,
        frames=frames,
        interval=1000 / fps,
        repeat=True,
    )


@xr.register_dataarray_accessor("epoch")
class EpochAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def animate(self, *args, **kwargs) -> FuncAnimation:
        """Generate animations of Epoch data.

        Parameters
        ----------
        args
            Positional arguments passed to :func:`generate_animation`.
        kwargs
            Keyword arguments passed to :func:`generate_animation`.

        Examples
        --------
        >>> import xarray as xr
        >>> from sdf_xarray import SDFPreprocess
        >>> ds = xr.open_mfdataset("*.sdf", preprocess=SDFPreprocess())
        >>> ani = ds["Electric_Field_Ey"].epoch.animate()
        >>> ani.save("myfile.mp4")
        """
        return animate(self._obj, *args, **kwargs)
