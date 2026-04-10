from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/3_3_Gaussian_1d_laser")

ds = sdfxr.open_dataset(input_dir / "0001.sdf")

# Convert the x and y coords to microns
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid"])

# Calculate Poynting flux magnitude
flux_magnitude = np.sqrt(
    ds["Derived_Poynting_Flux_x"] ** 2
    + ds["Derived_Poynting_Flux_y"] ** 2
    + ds["Derived_Poynting_Flux_z"] ** 2
)

# convert to W/cm^2
I_Wcm2 = flux_magnitude * 1e-4
I_Wcm2.attrs["long_name"] = "Poynting Flux Magnitude"
I_Wcm2.attrs["units"] = "W/cm$^2$"

I_Wcm2.epoch.plot()
plt.tight_layout()

plt.savefig(input_dir / "intensity.png", dpi=300)
np.savetxt(input_dir / "intensity_vals.txt", I_Wcm2.values)
np.savetxt(input_dir / "intensity_x.txt", ds["X_Grid_mid"].values)
