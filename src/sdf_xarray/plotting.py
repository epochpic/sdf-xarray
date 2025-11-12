from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

from types import MethodType

def get_frame_title(
    data: xr.DataArray,
    frame: int,
    display_sdf_name: bool = False,
    title_custom: str | None = None,
    t: str = "time",
) -> str:
    """Generate the title for a frame
    
    Parameters
    ----------
    data
        DataArray containing the target data
    frame
        Frame number
    display_sdf_name
        Display the sdf file name in the animation title
    title_custom
        Custom title to add to the plot
    t
        Time coordinate
    """

    # Adds custom text to the start of the title, if specified
    title_custom = "" if title_custom is None else f"{title_custom}, "
    # Adds the time axis and associated units to the title
    t_axis_value = data[t][frame].values

    t_axis_units = data[t].attrs.get("units", False)
    t_axis_units_formatted = f" [{t_axis_units}]" if t_axis_units else ""
    title_t_axis = f"{data[t].long_name} = {t_axis_value:.2e}{t_axis_units_formatted}"

    # Adds sdf name to the title, if specifed
    title_sdf = f", {frame:04d}.sdf" if display_sdf_name else ""
    return f"{title_custom}{title_t_axis}{title_sdf}"


def calculate_window_boundaries(
    data: xr.DataArray,
    xlim: tuple[float, float] | bool = False,
    x_axis_name: str = "X_Grid_mid",
    t: str = "time",
) -> np.ndarray:
    """Calculate the bounderies a moving window frame. If the user specifies xlim, this will
    be used as the initial bounderies and the window will move along acordingly.
    
    Parameters
    ----------
    data
        DataArray containing the target data
    xlim
        x limits
    x_axis_name
        Name of coordinate to assign to the x-axis
    t
        Time coordinate
    """
    x_grid = data[x_axis_name].values
    x_half_cell = (x_grid[1] - x_grid[0]) / 2
    N_frames = data[t].size

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
    
    Parameters
    ----------
    data
        DataArray containing the target data
    min_percentile
        Minimum percentile of the data
    max_percentile
        Maximum percentile of the data    
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
    t: str | None = None,
    ax: plt.Axes | None = None,
    **kwargs,
) -> FuncAnimation:
    """Generate an animation using an xarray.DataArray

    Parameters
    ---------
    data
        DataArray containing the target data
    fps
        Frames per second for the animation
    min_percentile
        Minimum percentile of the data
    max_percentile
        Maximum percentile of the data
    title
        Custom title to add to the plot
    display_sdf_name
        Display the sdf file name in the animation title
    t
        Coordinate for t axis (the coordinate which will be animated over). If `None`, use data.dims[0]
    ax
        Matplotlib axes on which to plot
    kwargs
        Keyword arguments to be passed to matplotlib

    Examples
    --------
    >>> ds["Derived_Number_Density_Electron"].epoch.animate()
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    kwargs_original = kwargs.copy()

    # Create plot if no ax is provided
    if ax is None:
        fig, ax = plt.subplots()
        plt.close(fig)

    # Makes a list of coordinates in data.
    coord_names = list(data.dims)
    if t is None:
        if "time" in coord_names:
            t = "time"
        else:
            t = coord_names[-1]
    coord_names.remove(t)

    N_frames = data[t].size
    global_min, global_max = compute_global_limits(data, min_percentile, max_percentile)

    if data.ndim == 2:
        kwargs.setdefault("x", coord_names[0])
        plot = data.isel({t:0}).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name, title, t))
        ax.set_ylim(global_min, global_max)

    if data.ndim == 3:
        kwargs.setdefault("norm", plt.Normalize(vmin = global_min, vmax = global_max))
        kwargs["add_colorbar"] = False
        # Set default x and y coordinates for 3D data if not provided
        kwargs.setdefault("x", coord_names[0])
        kwargs.setdefault("y", coord_names[1])

        # Finds the time step with the minimum data value
        # This is needed so that the animation can use the correct colour bar
        argmin_time = np.unravel_index(data.argmin(), data.shape)[0]
        
        # Initialize the plot, the final output will still start at the first time step
        plot = data.isel({t:argmin_time}).plot(ax = ax, **kwargs)
        ax.set_title(get_frame_title(data, 0, display_sdf_name, title, t))
        kwargs["cmap"] = plot.cmap

        # Add colorbar
        if kwargs_original.get("add_colorbar", True):
            long_name = data.attrs.get("long_name")
            units = data.attrs.get("units")
            fig = plot.get_figure()
            fig.colorbar(plot, ax=ax, label=f"{long_name} [{units}]")

    # check if there is a moving window by finding NaNs in the data
    move_window = np.isnan(np.sum(data.values))
    if move_window:
        window_boundaries = calculate_window_boundaries(data, kwargs.get("xlim", False), kwargs["x"])

    def update(frame):
        # Set the xlim for each frame in the case of a moving window
        if move_window:
            kwargs["xlim"] = window_boundaries[frame]

        # Update plot for the new frame
        ax.clear()

        plot = data.isel({t:frame}).plot(ax = ax, **kwargs)
        ax.set_title(get_frame_title(data, frame, display_sdf_name, title, t))

        if data.ndim == 2:
            ax.set_ylim(global_min, global_max)
        return plot
    
    return FuncAnimation(
        ax.get_figure(),
        update,
        frames = range(N_frames),
        interval = 1000 / fps,
        repeat = True,
    )

def show(anim):
    """Shows the FuncAnimation in a Jupyter notebook.
    
    Parameters
    ----------
    anim
        `matplotlib.animation.FuncAnimation`    
    """
    from IPython.display import HTML

    return HTML(anim.to_jshtml())

@xr.register_dataarray_accessor("epoch")
class EpochAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def animate(self, *args, **kwargs) -> FuncAnimation:
        """Generate animations of Epoch data.

        Parameters
        ----------
        args
            Positional arguments passed to :func:`animation`.
        kwargs
            Keyword arguments passed to :func:`animation`.

        Examples
        --------
        >>> anim = ds["Electric_Field_Ey"].epoch.animate()
        >>> anim.save("myfile.mp4")
        >>> # Or in a jupyter notebook:
        >>> anim.show()
        """

        # Add anim.show() functionality
        # anim.show() will display the animation in a jupyter notebook
        anim = animate(self._obj, *args, **kwargs)
        anim.show = MethodType(show, anim)

        return anim
