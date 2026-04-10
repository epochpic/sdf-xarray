from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/4_4_momentum_distribution")
ds = sdfxr.open_dataset(input_dir / "0000.sdf", keep_particles=True)
px = ds["Particles_Px_Electron_user"].values

bin_edges = np.linspace(px.min(), px.max(), 101)
bin_N, _ = np.histogram(
    px, bins=bin_edges, weights=ds["Particles_Weight_Electron_user"]
)
dpx = np.diff(bin_edges)
dN_dpx = bin_N / dpx
bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])

plt.plot(bin_centres, dN_dpx)
plt.xlabel("Px [kg.m/s]")
plt.ylabel("dN/dp$_x$ [s/(kg.m)]")

plt.savefig(input_dir / "px_spectrum.png", dpi=300)
np.savetxt(input_dir / "px_spectrum_vals.txt", dN_dpx)
np.savetxt(input_dir / "ke_spectrum_px.txt", bin_centres)
