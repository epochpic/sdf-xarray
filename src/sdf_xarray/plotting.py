from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from IPython.display import HTML
from matplotlib.animation import FuncAnimation


def get_frame_title(dataset: xr.Dataset, frame: int, display_sdf_name: bool) -> str:
    """Generate the title for a frame"""
    sdf_name = f", {frame:04d}.sdf" if display_sdf_name else ""
    time = dataset.isel(time=frame)["time"].to_numpy()
    return f"t = {time:.2e}s{sdf_name}"


def calculate_window_velocity_and_edges(
    dataset, target_attribute, time_since_start, x_axis_coord
):
    """Calculate the moving window's velocity and initial edges.

    1. Finds a lineout of the target atribute in the x coordinate of the first frame
    2. Removes the NaN values to isolate the simulation window
    3. Produces the index size of the window, indexed at zero
    4. Uses distance moved and final time of the simulation to calculate velocity and initial xlims
    """
    target_lineout = dataset[target_attribute].values[0, :, 0]
    target_lineout_window = target_lineout[~np.isnan(target_lineout)]
    x_grid = dataset[x_axis_coord].values
    window_size_index = target_lineout_window.size - 1

    velocity_window = (x_grid[-1] - x_grid[window_size_index]) / time_since_start[-1]
    initial_window_edge = (x_grid[0], x_grid[window_size_index])
    return velocity_window, initial_window_edge


def generate_animation(
    dataset: xr.Dataset,
    target_attribute: str,
    folder_path: Optional[str] = None,
    display: bool = False,
    display_sdf_name: bool = False,
    fps: int = 10,
    move_window: bool = False,
    **kwargs,
) -> Optional[HTML]:
    """Generate an animation for the given target attribute

    Arguments
    ---------
        dataset:
            The dataset containing the simulation data
        target_attribute:
            The attribute to plot for each timestep
        folder_path:
            The path to save the generated animation (default: None)
        display:
            Whether to display the animation in the notebook (default: False)
        display_sdf_name:
            Display the sdf file name in the animation title
        fps:
            Frames per second for the animation (default: 10)
        move_window:
            If the simulation has a moving window, the animation will move along with it (default: False)
        kwargs:
            Dictionary of variables from matplotlib
    Examples
    --------
    >>> generateAnimation(dataset, "Derived_Number_Density_Electron")
    """
    fig, ax = plt.subplots()
    N_frames = dataset.sizes.get("time")

    # Time since the first frame of the simulation
    time_since_start = dataset["time"].values - dataset["time"].values[0]

    target_values = dataset[target_attribute].values

    # Removes all NaNs from the target attribute values so that we can
    # compute the 1st and 99th percentiles to exclude extreme outliers.
    # This is then used to normilize the global colour bar
    target_values_no_nan = target_values[~np.isnan(target_values)]
    global_min = np.percentile(target_values_no_nan, 1)
    global_max = np.percentile(target_values_no_nan, 99)
    norm = plt.Normalize(vmin=global_min, vmax=global_max)

    if "x" not in kwargs:
        kwargs["x"] = "X_Grid_mid"
    if "y" not in kwargs:
        kwargs["y"] = "Y_Grid_mid"

    # Initialize the plot with the first timestep
    plot = dataset.isel(time=0)[target_attribute].plot(
        ax=ax, norm=norm, add_colorbar=False, **kwargs
    )

    title = get_frame_title(dataset, 0, display_sdf_name)
    ax.set_title(title)
    cbar = plt.colorbar(plot, ax=ax)
    cbar.set_label(
        f'{dataset[target_attribute].attrs.get("long_name")} [${dataset[target_attribute].attrs.get("units")}$]'
    )

    window_initial_edge = (0, 0)

    if move_window:
        window_velocity, window_initial_edge = calculate_window_velocity_and_edges(
            dataset, target_attribute, time_since_start, kwargs["x"]
        )

    # User's choice for initial window edge supercides the one calculated
    if "xlim" in kwargs:
        window_initial_edge = kwargs["xlim"]

    def update(frame):
        ax.clear()

        # Set the xlim for each frame in the case of a moving window
        if move_window:
            kwargs["xlim"] = (
                window_initial_edge[0] + window_velocity * time_since_start[frame],
                window_initial_edge[1] * 0.99
                + window_velocity * time_since_start[frame],
            )

        # Update plot for the new frame
        dataset.isel(time=frame)[target_attribute].plot(
            ax=ax, norm=norm, add_colorbar=False, **kwargs
        )
        title = get_frame_title(dataset, frame, display_sdf_name)
        ax.set_title(title)

    ani = FuncAnimation(
        fig,
        update,
        frames=range(N_frames),
        interval=1000 / fps,
        repeat=True,
    )

    # Save the animation
    if folder_path:
        try:
            ani.save(
                f"{folder_path}/{target_attribute.replace('/', '_')}.mp4",
                writer="ffmpeg",
                fps=fps,
            )
            print(
                f"Animation saved as MP4 at {folder_path}/{target_attribute.replace('/', '_')}.mp4"
            )
        except Exception as e:
            print(f"Failed to save as MP4 due to {e}. Falling back to GIF.")
            # Save as HTML
            ani.save(
                f"{folder_path}/{target_attribute.replace('/', '_')}.gif",
                writer="pillow",
                fps=fps,
            )
            print(
                f"Animation saved as GIF at {folder_path}/{target_attribute.replace('/', '_')}.mp4"
            )

    # Close the figure to avoid displaying the first frame as a separate plot
    plt.close(fig)

    if display:
        return HTML(ani.to_jshtml())
    return None
