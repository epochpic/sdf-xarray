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
    **kwargs,
) -> FuncAnimation:
    """Generate an animation

    Parameters
    ---------
    data
        The dataarray containing the target data
    fps
        Frames per second for the animation (default: 10)
    min_percentile
        Minimum percentile of the data (default: 0)
    max_percentile
        Maximum percentile of the data (default: 100)
    title
        Custom title to add to the plot.
    display_sdf_name
        Display the sdf file name in the animation title
    ax
        Matplotlib axes on which to plot.
    kwargs
        Keyword arguments to be passed to matplotlib.

    Examples
    --------
    >>> dataset["Derived_Number_Density_Electron"].epoch.animate()
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    kwargs_original = kwargs.copy()

    if ax is None:
        _, ax = plt.subplots()

    N_frames = data["time"].size
    global_min, global_max = compute_global_limits(data, min_percentile, max_percentile)

    # Initialise plot and set y-limits for 1D data
    if data.ndim == 2:
        kwargs.setdefault("x", "X_Grid_mid")
        plot = data.isel(time=0).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name, title))
        ax.set_ylim(global_min, global_max)

    # Initilise plot and set colour bar for 2D data
    if data.ndim == 3:
        kwargs["norm"] = plt.Normalize(vmin=global_min, vmax=global_max)
        kwargs["add_colorbar"] = False
        # Set default x and y coordinates for 2D data if not provided
        kwargs.setdefault("x", "X_Grid_mid")
        kwargs.setdefault("y", "Y_Grid_mid")

        # Initialize the plot with the first timestep
        plot = data.isel(time=0).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name, title))

        # Add colorbar
        if kwargs_original.get("add_colorbar", True):
            long_name = data.attrs.get("long_name")
            units = data.attrs.get("units")
            plt.colorbar(plot, ax=ax, label=f"{long_name} [${units}$]")

    # check if there is a moving window by finding NaNs in the data
    move_window = np.isnan(np.sum(data.values))
    if move_window:
        window_boundaries = calculate_window_boundaries(data, kwargs.get("xlim", False))

    def update(frame):
        # Set the xlim for each frame in the case of a moving window
        if move_window:
            kwargs["xlim"] = window_boundaries[frame]

        # Update plot for the new frame
        ax.clear()

        data.isel(time=frame).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, frame, display_sdf_name, title))

        # Update y-limits for 1D data
        if data.ndim == 2:
            ax.set_ylim(global_min, global_max)

    return FuncAnimation(
        ax.get_figure(),
        update,
        frames=range(N_frames),
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
