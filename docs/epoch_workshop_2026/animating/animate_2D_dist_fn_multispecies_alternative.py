from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import sdf_xarray as sdfxr

input_dir = Path("datasets/2_1_two_stream_instability")
ds = sdfxr.open_mfdataset(
    input_dir, data_vars=["dist_fn_x_px_Left", "dist_fn_x_px_Right"]
)

# Rescale coords to account for kilometers
ds = ds.epoch.rescale_coords(1e-3, "km", ["X_x_px_Left"])

# Sum phase-space of species "Left" and "Right" in "x_px" distribution function
# NOTE: We only use the values from the right distribution function as if we inherit
# the coords we from the right we end up with 4 coords instead of 2
total_phase_space = ds["dist_fn_x_px_Left"] + ds["dist_fn_x_px_Right"].values
total_phase_space.attrs["long_name"] = "Phase Space Distribution"
total_phase_space.attrs["units"] = "kg.m/s"

fig, ax = plt.subplots()

# construct first frame
# Data needs to be transposed so that axes match
total_phase_space = total_phase_space.T
col_min = total_phase_space.values.min()
col_max = total_phase_space.values.max()
gif_frame = ax.pcolormesh(
    total_phase_space["X_x_px_Left"],
    total_phase_space["Px_x_px_Left"],
    total_phase_space.isel(time=0),
    vmin=col_min,
    vmax=col_max,
)
ax.set_xlabel(
    f"{total_phase_space['X_x_px_Left'].attrs['long_name']} [{total_phase_space['X_x_px_Left'].attrs['units']}]"
)
ax.set_ylabel(
    f"{total_phase_space.attrs['long_name']} [{total_phase_space.attrs['units']}]"
)
ax.set_title(f"t = {ds['time'].values[0]:.3f} [{ds['time'].attrs['units']}]")
cbar = fig.colorbar(gif_frame, ax=ax)
cbar.set_label("Summed particle weight per bin")


# Make GIF
def update(i):
    gif_frame.set_array(total_phase_space.isel(time=i))
    ax.set_title(f"t = {ds['time'].values[i]:.3f} [{ds['time'].attrs['units']}]")
    return (gif_frame,)


anim = FuncAnimation(fig, update, frames=ds.sizes["time"])
anim.save(input_dir / "phase_space.gif")
