from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


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


def get_axis_label(dim: xr.DataArray):
    return f"{dim.long_name} [{dim.units}]"


def _recover_vertex_coord(w_mid):
    # Takes a midpoint coordinate, returns a vertex coordinate
    w_size = w_mid.size
    dw = w_mid[1] - w_mid[0]
    w = np.zeros(w_mid.size + 1)
    w[:w_size] = w_mid - dw / 2
    w[w_size] = w[w_size - 1] + dw
    return w


def shift_cmap(cmap, vmin, vmax, vcenter, N=1024):
    """
    Creates a new colourmap where the visual center of the original
    colourmap is shifted to a specific data value.
    """
    import matplotlib.colors as mc  # noqa: PLC0415
    import matplotlib.pyplot as plt  # noqa: PLC0415

    # get the original colourmap
    if type(cmap) is str:
        cmap = plt.get_cmap(cmap)

    midpoint = (vcenter - vmin) / (vmax - vmin)
    lower_size = int(N * midpoint)
    upper_size = N - lower_size

    bottom_colors = cmap(np.linspace(0.0, 0.5, lower_size))
    top_colors = cmap(np.linspace(0.5, 1.0, upper_size))
    new_colors = np.vstack((bottom_colors, top_colors))

    return mc.ListedColormap(new_colors, name=f"shifted_{cmap.name}")


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


def voxel_plot(
    da: xr.DataArray,
    vmin: float | None = None,
    vmax: float | None = None,
    vcenter: float | None = None,
    mask: list[bool] | None = None,
    xlim: tuple[float | None, float | None] = (None, None),
    ylim: tuple[float | None, float | None] = (None, None),
    zlim: tuple[float | None, float | None] = (None, None),
    aspect: Literal["equal"] | Literal["auto"] = "equal",
    elev: int = 30,
    azim: int = -60,
    cmap: str = "viridis",
    cbar_scale: float = 0.9,
    **kwargs,
) -> tuple[Figure, Axes]:
    """
    Will take 3 dimensional data and plot it as voxels.

    Parameters
    ----------
    da
        DataArray to be plotted.
    vmin
        Minimum value. If `mask` is not stated, will be used to define the mask.
    vmax
        Maximum value. If `mask` is not stated, will be used to define the mask.
    vcenter
        Center value of the colourmap. Useful for diverging colourmaps with non-symetrical data.
    mask
        Array of bools specifing which cells to show. Must be same size as `da`
    xlim, ylim, zlim
        Sets the limits of the plot.
    aspect
        Aspect ratio of the plot. "equal", "auto" or list of floats. (default = "equal")
    elev
        Elevation angle in degrees. (default = 30)
    azim
        Azimithul angle in degrees. (default = -60)
    cmap
        Colourmap (default = "viridis")
    cbar_scale
        Vertical scale of the colorbar (default = 0.9)
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415

    print("Warning! voxel plots can be extremely intensive!")

    # Limit arrays based on axis limits
    da = da.epoch.limit((xlim, ylim, zlim))

    dims = da.dims

    # Create W_Grid from W_Grid_mid coords
    x = _recover_vertex_coord(da[dims[0]])
    y = _recover_vertex_coord(da[dims[1]])
    z = _recover_vertex_coord(da[dims[2]])

    # Create mesh
    x_mesh, y_mesh, z_mesh = np.meshgrid(x, y, z, indexing="ij")

    if vmin is None:
        vmin = np.min(da.values)
    if vmax is None:
        vmax = np.max(da.values)

    # Mask out data
    if mask is None:
        mask = (da > vmin) * (da < vmax)

    # Plot the data array
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection="3d")
    ax.view_init(elev, azim)

    # Set axis labels
    ax.set_xlabel(get_axis_label(da[dims[0]]))
    ax.set_ylabel(get_axis_label(da[dims[1]]))
    ax.set_zlabel(get_axis_label(da[dims[2]]))

    # Find and set axis limits
    xlim, ylim, zlim = [
        (data.min() if low is None else low, data.max() if high is None else high)
        for (low, high), data in zip([xlim, ylim, zlim], [x, y, z])
    ]

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_zlim(zlim)

    # Compute and set the box aspect ratio
    if aspect == "equal":
        box_aspect = (1, 1, 1)
    elif aspect == "auto":
        box_aspect = (xlim[1] - xlim[0], ylim[1] - ylim[0], zlim[1] - zlim[0])
    else:
        box_aspect = aspect

    ax.set_box_aspect(box_aspect)

    # Colour bar and colour map
    if vcenter is not None:
        cmap = shift_cmap(cmap, vmin, vmax, vcenter)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap)
    colours = cmap(norm(da))

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Required for the colorbar to function
    cbar_label = get_axis_label(da)
    fig.colorbar(sm, ax=ax, label=cbar_label, shrink=cbar_scale, aspect=20 * cbar_scale)

    ax.voxels(x_mesh, y_mesh, z_mesh, mask, facecolors=colours, **kwargs)

    return fig, ax


def _setup_line_plot(
    data: xr.DataArray,
    ax: plt.Axes,
    coord_names: list[str],
    kwargs: dict,
    axis_kwargs: dict,
    min_percentile: float,
    max_percentile: float,
    t: str,
) -> tuple[float, float]:
    """Line animation initialization."""

    kwargs.setdefault("x", coord_names[0])

    data.isel({t: 0}).plot(ax=ax, **kwargs)

    global_min, global_max = compute_global_limits(data, min_percentile, max_percentile)

    _set_axes_labels(ax, axis_kwargs)

    if "ylim" not in kwargs:
        ax.set_ylim(global_min, global_max)

    return global_min, global_max


def _setup_pcolormesh_plot(
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
    """pcolormesh animation initialization."""
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


def _setup_voxel_plot(
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
    """
    Voxel animation initialization.
    NOTE: this function exists for completeness, voxel plots don't work in animations yet
    """
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
        global_min, global_max = _setup_line_plot(
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
        _setup_pcolormesh_plot(
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
    elif data.ndim == 4:
        raise NotImplementedError("Voxel animations are not currently supported.")
        # _setup_voxel_plot(
        #     data=data,
        #     ax=ax,
        #     coord_names=coord_names,
        #     kwargs=kwargs,
        #     kwargs_original=kwargs_original,
        #     axis_kwargs=axis_kwargs,
        #     min_percentile=min_percentile,
        #     max_percentile=max_percentile,
        #     t=t,
        # )

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
    of this function is via `sdf_xarray.dataarray_accessor.EpochAccessor.animate`.

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
    >>> anim = ds["Derived_Number_Density_Electron"].epoch.animate()
    >>> anim.save("animation.gif")
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.animation import FuncAnimation  # noqa: PLC0415

    # Create plot if no ax is provided
    if ax is None:
        _, ax = plt.subplots()

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
        _, ax = plt.subplots()

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
