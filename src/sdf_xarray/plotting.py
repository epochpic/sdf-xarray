from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation


def get_frame_title(data: xr.DataArray, frame: int, display_sdf_name: bool) -> str:
    """Generate the title for a frame"""
    sdf_name = f", {frame:04d}.sdf" if display_sdf_name else ""
    time = data["time"][frame].to_numpy()
    return f"t = {time:.2e}s{sdf_name}"


def calculate_window_velocity_and_edges(
    data: xr.DataArray, x_axis_coord: str
) -> tuple[float, tuple[float, float], np.ndarray]:
    """Calculate the moving window's velocity and initial edges.

    1. Finds a lineout of the target atribute in the x coordinate of the first frame
    2. Removes the NaN values to isolate the simulation window
    3. Produces the index size of the window, indexed at zero
    4. Uses distance moved and final time of the simulation to calculate velocity and initial xlims
    """
    time_since_start = data["time"].values - data["time"].values[0]
    initial_window_edge = (0, 0)
    target_lineout = data.values[0, :, 0]
    target_lineout_window = target_lineout[~np.isnan(target_lineout)]
    x_grid = data[x_axis_coord].values
    window_size_index = target_lineout_window.size - 1

    velocity_window = (x_grid[-1] - x_grid[window_size_index]) / time_since_start[-1]
    initial_window_edge = (x_grid[0], x_grid[window_size_index])
    return velocity_window, initial_window_edge, time_since_start


def compute_global_limits(data: xr.DataArray) -> tuple[float, float]:
    """Remove all NaN values from the target data to calculate the 1st and 99th percentiles,
    excluding extreme outliers.
    """
    values_no_nan = data.values[~np.isnan(data.values)]
    global_min = np.percentile(values_no_nan, 1)
    global_max = np.percentile(values_no_nan, 99)
    return global_min, global_max


def is_1d(data: xr.DataArray) -> bool:
    """Check if the data is 1D."""
    return len(data.shape) == 2


def is_2d(data: xr.DataArray) -> bool:
    """Check if the data is 2D or 3D."""
    return len(data.shape) == 3


def generate_animation(
    data: xr.DataArray,
    display_sdf_name: bool = False,
    fps: int = 10,
    move_window: bool = False,
    ax: plt.Axes | None = None,
    **kwargs,
) -> FuncAnimation:
    """Generate an animation

    Parameters
    ---------
    dataset
        The dataset containing the simulation data
    target_attribute
        The attribute to plot for each timestep
    display_sdf_name
        Display the sdf file name in the animation title
    fps
        Frames per second for the animation (default: 10)
    move_window
        If the simulation has a moving window, the animation will move along
        with it (default: False)
    ax
        Matplotlib axes on which to plot.
    kwargs
        Keyword arguments to be passed to matplotlib.

    Examples
    --------
    >>> generate_animation(dataset["Derived_Number_Density_Electron"])
    """
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    if ax is None:
        _, ax = plt.subplots()

    N_frames = data["time"].size
    global_min, global_max = compute_global_limits(data)

    if is_2d(data):
        kwargs["norm"] = plt.Normalize(vmin=global_min, vmax=global_max)
        kwargs["add_colorbar"] = False
        # Set default x and y coordinates for 2D data if not provided
        kwargs.setdefault("x", "X_Grid_mid")
        kwargs.setdefault("y", "Y_Grid_mid")

        # Initialize the plot with the first timestep
        plot = data.isel(time=0).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name))

        # Add colorbar
        long_name = data.attrs.get("long_name")
        units = data.attrs.get("units")
        plt.colorbar(plot, ax=ax, label=f"{long_name} [${units}$]")

    # Initialise plo and set y-limits for 1D data
    if is_1d(data):
        plot = data.isel(time=0).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name))
        ax.set_ylim(global_min, global_max)

    if move_window:
        window_velocity, window_initial_edge, time_since_start = (
            calculate_window_velocity_and_edges(data, kwargs["x"])
        )

    # User's choice for initial window edge supercides the one calculated
    if "xlim" in kwargs:
        window_initial_edge = kwargs["xlim"]

    def update(frame):
        # Set the xlim for each frame in the case of a moving window
        if move_window:
            kwargs["xlim"] = (
                window_initial_edge[0] + window_velocity * time_since_start[frame],
                window_initial_edge[1] * 0.99
                + window_velocity * time_since_start[frame],
            )

        # Update plot for the new frame
        ax.clear()
        data.isel(time=frame).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, frame, display_sdf_name))

        # # Update y-limits for 1D data
        if is_1d(data):
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
        return generate_animation(self._obj, *args, **kwargs)
