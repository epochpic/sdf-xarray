# sdf-xarray

`sdf-xarray` provides a backend for [xarray](https://xarray.dev) to
read SDF files as created by the [EPOCH](https://epochpic.github.io)
plasma PIC code.

## Installation

Until this is on PyPI, please install directly from this repo:

```
pip install git+https://github.com/PlasmaFAIR/sdf-xarray.git@main
```

or from a local checkout:

```
git clone https://github.com/PlasmaFAIR/sdf-xarray.git
cd sdf-xarray
pip install .
```

## Usage

`sdf-xarray` is a backend for xarray, and so is usable directly from
xarray:

### Single file loading
```python
import xarray as xr
from sdf_xarray import SDFPreprocess

df = xr.open_dataset("0010.sdf")

print(df["Electric Field/Ex"])

# <xarray.DataArray 'Electric Field/Ex' (X_x_px_deltaf/electron_beam: 16)> Size: 128B
# [16 values with dtype=float64]
# Coordinates:
#   * X_x_px_deltaf/electron_beam  (X_x_px_deltaf/electron_beam) float64 128B 1...
# Attributes:
#     units:    V/m
```

### Multi file loading
```python
ds = xr.open_mfdataset(
    "*.sdf",
    combine="nested",
    data_vars='minimal', 
    coords='minimal', 
    compat='override', 
    preprocess=SDFPreprocess()
)

print(ds)

# Dimensions:
# time: 301, X_Grid_mid: 128, Y_Grid_mid: 128, Px_px_py/Photon: 200, Py_px_py/Photon: 200, X_Grid: 129, Y_Grid: 129, Px_px_py/Photon_mid: 199, Py_px_py/Photon_mid: 199
# Coordinates: (9)
# Data variables: (18)
# Indexes: (9)
# Attributes: (22)
```
