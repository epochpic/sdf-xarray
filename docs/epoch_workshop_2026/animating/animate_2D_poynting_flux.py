from pathlib import Path

import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/3_5_Gaussian_beam")
ds = sdfxr.open_mfdataset(input_dir)

# Convert the time to femtoseconds
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
# Convert the x and y coords to microns
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])

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

anim = I_Wcm2.epoch.animate()

# Visualise it in a Jupyter notebook
anim.show()

# Or save the animation
# anim.save(input_dir / "laser.gif", fps=10)
