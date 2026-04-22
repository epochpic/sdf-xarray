from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sdf_xarray as sdfxr

# Constants
mass = 9.1093837e-31
c = 299792458
q0 = 1.60217663e-19

input_dir = Path("datasets/4_3_basic_target")
ds = sdfxr.open_dataset(input_dir / "0000.sdf", keep_particles=True)
particles_magnitude = (
    ds["Particles_Px_Electron"] ** 2
    + ds["Particles_Py_Electron"] ** 2
    + ds["Particles_Pz_Electron"] ** 2
)
ke_MeV = (np.sqrt(particles_magnitude * c**2 + mass**2 * c**4) - mass * c**2) / (
    1.0e6 * q0
)

bin_edges = np.linspace(ke_MeV.min().values, ke_MeV.max().values, 101)
bin_N, _ = np.histogram(
    ke_MeV.values, bins=bin_edges, weights=ds["Particles_Weight_Electron"]
)
dKE = np.diff(bin_edges)
dN_dKE = bin_N / dKE
bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])

plt.plot(bin_centres, dN_dKE)
plt.xlabel("Kinetic energy [MeV]")
plt.ylabel("dN/dKE [1/MeV]")

plt.savefig(input_dir / "ke_spectrum.png", dpi=300)
np.savetxt(input_dir / "ke_spectrum_vals.txt", ke_MeV.values)
np.savetxt(input_dir / "ke_spectrum_ke.txt", bin_centres)
