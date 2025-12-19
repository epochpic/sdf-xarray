from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from types import MethodType
from typing import TYPE_CHECKING, Any

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation


@dataclass
class AnimationUnit:
    update: Callable[[int], object]
    n_frames: int


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
    xlim: tuple[float, float] | None = None,
    x_axis_name: str = "X_Grid_mid",
    t: str = "time",
) -> np.ndarray:
    """Calculate the boundaries a moving window frame. If the user specifies xlim, this will
    be used as the initial boundaries and the window will move along acordingly.

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
    n_frames = data[t].size

    # Find the window boundaries by finding the first and last non-NaN values in the 0th lineout
    # along the x-axis.
    window_boundaries = np.zeros((n_frames, 2))
    for i in range(n_frames):
        # Check if data is 1D
        if data.ndim == 2:
            target_lineout = data[i].values
        # Check if data is 2D
        if data.ndim == 3:
            target_lineout = data[i, :, 0].values
        x_grid_non_nan = x_grid[~np.isnan(target_lineout)]
        window_boundaries[i, 0] = x_grid_non_nan[0] - x_half_cell
        window_boundaries[i, 1] = x_grid_non_nan[-1] + x_half_cell

    # User's choice for initial window edge supercedes the one calculated
    if xlim is not None:
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


def _set_axes_labels(ax: plt.Axes, axis_kwargs: dict) -> None:
    """Set the labels for the x and y axes"""
    if "xlabel" in axis_kwargs:
        ax.set_xlabel(axis_kwargs["xlabel"])
    if "ylabel" in axis_kwargs:
        ax.set_ylabel(axis_kwargs["ylabel"])


def _setup_2d_plot(
    data: xr.DataArray,
    ax: plt.Axes,
    coord_names: list[str],
    kwargs: dict,
    axis_kwargs: dict,
    min_percentile: float,
    max_percentile: float,
    t: str,
) -> tuple[float, float]:
    """Setup 2D plot initialization."""

    kwargs.setdefault("x", coord_names[0])

    data.isel({t: 0}).plot(ax=ax, **kwargs)

    global_min, global_max = compute_global_limits(data, min_percentile, max_percentile)

    _set_axes_labels(ax, axis_kwargs)

    if "ylim" not in kwargs:
        ax.set_ylim(global_min, global_max)

    return global_min, global_max


def _setup_3d_plot(
    data: xr.DataArray,
    ax: plt.Axes,
    coord_names: list[str],
    kwargs: dict,
    kwargs_original: dict,
    axis_kwargs: dict,
    min_percentile: float,
    max_percentile: float,
    t: str,
) -> None:
    """Setup 3D plot initialization."""
    import matplotlib.pyplot as plt  # noqa: PLC0415

    if "norm" not in kwargs:
        global_min, global_max = compute_global_limits(
            data, min_percentile, max_percentile
        )
        kwargs["norm"] = plt.Normalize(vmin=global_min, vmax=global_max)

    kwargs["add_colorbar"] = False
    kwargs.setdefault("x", coord_names[0])
    kwargs.setdefault("y", coord_names[1])

    argmin_time = np.unravel_index(np.argmin(data.values), data.shape)[0]
    plot = data.isel({t: argmin_time}).plot(ax=ax, **kwargs)
    kwargs["cmap"] = plot.cmap

    _set_axes_labels(ax, axis_kwargs)

    if kwargs_original.get("add_colorbar", True):
        long_name = data.attrs.get("long_name")
        units = data.attrs.get("units")
        fig = plot.get_figure()
        fig.colorbar(plot, ax=ax, label=f"{long_name} [{units}]")


def _generate_animation(
    data: xr.DataArray,
    clear_axes: bool = False,
    min_percentile: float = 0,
    max_percentile: float = 100,
    title: str | None = None,
    display_sdf_name: bool = False,
    move_window: bool = False,
    t: str | None = None,
    ax: plt.Axes | None = None,
    kwargs: dict | None = None,
) -> AnimationUnit:
    """
    Internal function for generating the plotting logic required for animations.

    Parameters
    ---------
    data
        DataArray containing the target data
    clear_axes
        Decide whether to run ``ax.clear()`` in every update
    min_percentile
        Minimum percentile of the data
    max_percentile
        Maximum percentile of the data
    title
        Custom title to add to the plot
    display_sdf_name
        Display the sdf file name in the animation title
    move_window
        Update the ``xlim`` to be only values that are not NaNs at each time interval
    t
        Coordinate for t axis (the coordinate which will be animated over).
        If ``None``, use ``data.dims[0]``
    ax
        Matplotlib axes on which to plot
    kwargs
        Keyword arguments to be passed to matplotlib

    Examples
    --------
    >>> anim = animate(ds["Derived_Number_Density_Electron"])
    >>> anim.save("animation.gif")
    """

    if kwargs is None:
        kwargs = {}
    kwargs_original = kwargs.copy()

    axis_kwargs = {}
    for key in ("xlabel", "ylabel"):
        if key in kwargs:
            axis_kwargs[key] = kwargs.pop(key)

    # Sets the animation coordinate (t) for iteration. If time is in the coords
    # then it will set time to be t. If it is not it will fallback to the last
    # coordinate passed in. By default coordinates are passed in from xarray in
    # the form x, y, z so in order to preserve the x and y being on their
    # respective axes we animate over the final coordinate that is passed in
    # which in this example is z
    coord_names = list(data.dims)
    if t is None:
        t = "time" if "time" in coord_names else coord_names[-1]
    coord_names.remove(t)

    N_frames = data[t].size

    global_min = global_max = None
    if data.ndim == 2:
        global_min, global_max = _setup_2d_plot(
            data=data,
            ax=ax,
            coord_names=coord_names,
            kwargs=kwargs,
            axis_kwargs=axis_kwargs,
            min_percentile=min_percentile,
            max_percentile=max_percentile,
            t=t,
        )
    elif data.ndim == 3:
        _setup_3d_plot(
            data=data,
            ax=ax,
            coord_names=coord_names,
            kwargs=kwargs,
            kwargs_original=kwargs_original,
            axis_kwargs=axis_kwargs,
            min_percentile=min_percentile,
            max_percentile=max_percentile,
            t=t,
        )

    ax.set_title(get_frame_title(data, 0, display_sdf_name, title, t))

    window_boundaries = None
    if move_window:
        window_boundaries = calculate_window_boundaries(
            data, kwargs.get("xlim"), kwargs["x"]
        )

    def update(frame):
        if clear_axes:
            ax.clear()
        # Set the xlim for each frame in the case of a moving window
        if move_window:
            kwargs["xlim"] = window_boundaries[frame]

        plot = data.isel({t: frame}).plot(ax=ax, **kwargs)
        ax.set_title(get_frame_title(data, frame, display_sdf_name, title, t))
        _set_axes_labels(ax, axis_kwargs)

        if data.ndim == 2 and "ylim" not in kwargs and global_min is not None:
            ax.set_ylim(global_min, global_max)

        return plot

    return AnimationUnit(
        update=update,
        n_frames=N_frames,
    )


def animate(
    data: xr.DataArray,
    fps: float = 10,
    min_percentile: float = 0,
    max_percentile: float = 100,
    title: str | None = None,
    display_sdf_name: bool = False,
    move_window: bool = False,
    t: str | None = None,
    ax: plt.Axes | None = None,
    **kwargs,
) -> FuncAnimation:
    """
    Generate an animation using an `xarray.DataArray`. The intended use
    of this function is via `sdf_xarray.plotting.EpochAccessor.animate`.

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
    move_window
        Update the ``xlim`` to be only values that are not NaNs at each time interval
    t
        Coordinate for t axis (the coordinate which will be animated over).
        If ``None``, use ``data.dims[0]``
    ax
        Matplotlib axes on which to plot
    kwargs
        Keyword arguments to be passed to matplotlib

    Examples
    --------
    >>> anim = animate(ds["Derived_Number_Density_Electron"])
    >>> anim.save("animation.gif")
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    # Create plot if no ax is provided
    if ax is None:
        fig, ax = plt.subplots()
        # Prevents figure from prematurely displaying in Jupyter notebook
        plt.close(fig)

    animation = _generate_animation(
        data,
        clear_axes=True,
        min_percentile=min_percentile,
        max_percentile=max_percentile,
        title=title,
        display_sdf_name=display_sdf_name,
        move_window=move_window,
        t=t,
        ax=ax,
        kwargs=kwargs,
    )

    return FuncAnimation(
        ax.get_figure(),
        animation.update,
        frames=range(animation.n_frames),
        interval=1000 / fps,
        repeat=True,
    )


def animate_multiple(
    *datasets: xr.DataArray,
    datasets_kwargs: list[dict[str, Any]] | None = None,
    fps: float = 10,
    min_percentile: float = 0,
    max_percentile: float = 100,
    title: str | None = None,
    display_sdf_name: bool = False,
    move_window: bool = False,
    t: str | None = None,
    ax: plt.Axes | None = None,
    **common_kwargs,
) -> FuncAnimation:
    """
    Generate an animation using multiple `xarray.DataArray`. The intended use
    of this function is via `sdf_xarray.dataset_accessor.EpochAccessor.animate_multiple`.

    Parameters
    ---------
    datasets
        `xarray.DataArray` objects containing the data to be animated
    datasets_kwargs
       A list of dictionaries, following the same order as ``datasets``, containing
        per-dataset matplotlib keyword arguments. The list does not need to be the same
        length as ``datasets``; missing entries are initialised as empty dictionaries
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
    move_window
        Update the ``xlim`` to be only values that are not NaNs at each time interval
    t
        Coordinate for t axis (the coordinate which will be animated over). If ``None``,
        use ``data.dims[0]``
    ax
        Matplotlib axes on which to plot
    common_kwargs
        Matplotlib keyword arguments applied to all datasets. These are overridden by
        per-dataset entries in ``datasets_kwargs``

    Examples
    --------
    >>> anim = animate_multiple(
        ds["Derived_Number_Density_Electron"],
        ds["Derived_Number_Density_Ion"],
        datasets_kwargs=[{"label": "Electron"}, {"label": "Ion"}],
        ylim=(0e27,4e27),
        display_sdf_name=True,
        ylabel="Derived Number Density [1/m$^3$]"
    )
    >>> anim.save("animation.gif")
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    if not datasets:
        raise ValueError("At least one dataset must be provided")

    # Create plot if no ax is provided
    if ax is None:
        fig, ax = plt.subplots()
        # Prevents figure from prematurely displaying in Jupyter notebook
        plt.close(fig)

    n_datasets = len(datasets)
    if datasets_kwargs is None:
        # Initialise an empty series of dicts the same size as the number of datasets
        datasets_kwargs = [{} for _ in range(n_datasets)]
    else:
        # The user might only want to use kwargs on some of the datasets so we make sure
        # to initialise additional empty dicts and append them to the list
        datasets_kwargs.extend({} for _ in range(n_datasets - len(datasets_kwargs)))

    animations: list[AnimationUnit] = []
    for da, kw in zip(datasets, datasets_kwargs):
        animations.append(
            _generate_animation(
                da,
                ax=ax,
                min_percentile=min_percentile,
                max_percentile=max_percentile,
                title=title,
                display_sdf_name=display_sdf_name,
                move_window=move_window,
                t=t,
                # Per-dataset kwargs override common matplotlib kwargs
                kwargs={**common_kwargs, **kw},
            )
        )

    lengths = [anim.n_frames for anim in animations]
    n_frames = min(lengths)

    if len(set(lengths)) > 1:
        warnings.warn(
            "Datasets have different frame counts; truncating to the shortest",
            stacklevel=2,
        )

    # Render the legend if a label exists for any 2D dataset
    show_legend = any(
        "label" in kw and da.ndim == 2 for da, kw in zip(datasets, datasets_kwargs)
    )

    def update(frame):
        ax.clear()
        for anim in animations:
            anim.update(frame)
        if show_legend:
            ax.legend(loc="upper right")

    return FuncAnimation(
        ax.get_figure(),
        update,
        frames=range(n_frames),
        interval=1000 / fps,
        repeat=True,
    )


def show(anim):
    """Shows the FuncAnimation in a Jupyter notebook.

    Parameters
    ----------
    anim
        `matplotlib.animation.FuncAnimation`
    """
    from IPython.display import HTML  # noqa: PLC0415

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
        >>> anim.save("animation.gif")
        >>> # Or in a jupyter notebook:
        >>> anim.show()
        """

        # Add anim.show() functionality
        # anim.show() will display the animation in a jupyter notebook
        anim = animate(self._obj, *args, **kwargs)
        anim.show = MethodType(show, anim)

        return anim
