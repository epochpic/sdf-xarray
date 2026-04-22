from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

input_dir = Path("datasets/4_3_basic_target")

ds = sdfxr.open_dataset(input_dir / "0000.sdf")
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])

ds["Derived_Number_Density"].epoch.plot()
plt.tight_layout()

plt.savefig(input_dir / "number_density.png", dpi=300)
np.savetxt(input_dir / "number_density_vals.txt", ds["Derived_Number_Density"].values)
np.savetxt(input_dir / "number_density_x.txt", ds["X_Grid_mid"].values)
