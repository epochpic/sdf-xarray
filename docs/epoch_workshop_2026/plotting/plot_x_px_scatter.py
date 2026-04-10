from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/5_2_subsets")
ds = sdfxr.open_dataset(input_dir / "0000.sdf", keep_particles=True)

ds = ds.epoch.rescale_coords(
    1e6, "µm", ["X_Particles_subset_Refluxers_Electron", "Y_Target_mid"]
)

x = ds["X_Particles_subset_Refluxers_Electron"]
px = ds["Particles_Px_subset_Refluxers_Electron"]

plt.scatter(x, px)
plt.xlabel("x [µm]")
plt.ylabel("Px [kg.m/s]")

plt.savefig(input_dir / "x_px.png", dpi=300)
np.savetxt(input_dir / "x_px_vals.txt", px.values)
np.savetxt(input_dir / "x_px_x.txt", x.values)
