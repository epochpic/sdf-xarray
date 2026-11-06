import matplotlib.pyplot as plt

import sdf_xarray as sdfxr

plt.rcParams.update({"font.size": 13})

# Save a plot of a single SDF
ds = sdfxr.open_dataset("0010.sdf")
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])
ds["Electric_Field_Ey"].epoch.plot()
plt.tight_layout()
plt.savefig("Electric_Field_Ey.png", dpi=500)
plt.close()

# Generate the animation
ds = sdfxr.open_mfdataset("*.sdf")
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])

anim = ds["Electric_Field_Ey"].epoch.animate()
plt.tight_layout()
anim.save("Electric_Field_Ey.gif", fps=10, dpi=500)
plt.close()

# Generate 4 frames in place of the animation
plt.rcParams.update({"font.size": 16})
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 8))

flux_x = ds["Electric_Field_Ey"]
# Mimic the normalized colormap that would be built if this was an actual animation
norm = plt.Normalize(vmin=flux_x.min().values, vmax=flux_x.max().values)
flux_x.isel(time=5).epoch.plot(ax=ax1, norm=norm)
flux_x.isel(time=10).epoch.plot(ax=ax2, norm=norm)
flux_x.isel(time=15).epoch.plot(ax=ax3, norm=norm)
flux_x.isel(time=20).epoch.plot(ax=ax4, norm=norm)

plt.tight_layout()
fig.savefig("Electric_Field_Ey_frames.png", dpi=500)
