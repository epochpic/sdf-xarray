from pathlib import Path

import sdf_xarray as sdfxr

input_dir = Path("datasets/1_1_drifting_bunch")
ds = sdfxr.open_mfdataset(input_dir)

# Convert the time to femtoseconds
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
# Convert the x and y coords to microns
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid"])

anim = ds["Derived_Number_Density"].epoch.animate()

# Visualise it in a Jupyter notebook
anim.show()

# Or save the animation
# anim.save(input_dir / "number_density.gif", fps=5)
