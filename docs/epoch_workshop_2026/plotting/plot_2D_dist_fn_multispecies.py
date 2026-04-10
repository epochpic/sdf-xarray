from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/2_1_two_stream_instability")
ds = sdfxr.open_dataset(input_dir / "0000.sdf")

ds = ds.epoch.rescale_coords(1e-3, "km", ["X_x_px_Left"])

# Sum phase-space of species "Left" and "Right" in "x_px" distribution function
# NOTE: We only use the values from the right distribution function as if we inherit
# the coords we from the right we end up with 4 coords instead of 2
total_phase_space = ds["dist_fn_x_px_Left"] + ds["dist_fn_x_px_Right"].values
total_phase_space.attrs["long_name"] = "Summed Particle Weight Per Bin"
total_phase_space.attrs["units"] = ""

total_phase_space.epoch.plot()
plt.tight_layout()

plt.savefig(input_dir / "phase_space.png", dpi=300)
np.savetxt(input_dir / "phase_space_vals.txt", total_phase_space.values)
np.savetxt(input_dir / "phase_space_x.txt", ds["X_x_px_Left"].values)
np.savetxt(input_dir / "phase_space_y.txt", ds["Px_x_px_Left"].values)
