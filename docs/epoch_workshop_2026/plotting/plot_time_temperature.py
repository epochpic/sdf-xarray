from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

# Constants
kB = 1.380649e-23
q0 = 1.60217663e-19

input_dir = Path("datasets/4_2_self_heating")
ds = sdfxr.open_mfdataset(input_dir)

# Convert the time to femtoseconds
ds = ds.epoch.rescale_coords(1e15, "fs", "time")

# Averate temperature over all spatial cells at each time-step
kB = 1.380649e-23
q0 = 1.60217663e-19

temp_ev = ds["Derived_Temperature"].mean(dim=("X_Grid_mid", "Y_Grid_mid")) * kB / q0

temp_ev.epoch.plot()
plt.tight_layout()

plt.savefig(input_dir / "temperature_time.png", dpi=300)
np.savetxt(input_dir / "temperature_time_time.txt", temp_ev["time"].values)
np.savetxt(input_dir / "temperature_time_temperature.txt", temp_ev.values)
