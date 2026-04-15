from pathlib import Path

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

anim = total_phase_space.epoch.animate()
# Visualise it in a Jupyter notebook
anim.show()

# Or save the animation
# anim.save(input_dir / "phase_space.gif")
