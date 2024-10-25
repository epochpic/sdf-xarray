# sdf-xarray

`sdf-xarray` provides a backend for [xarray](https://xarray.dev) to
read SDF files as created by the [EPOCH](https://epochpic.github.io)
plasma PIC code.

> ![IMPORTANT]
> All variable names now use snake_case to align with Epoch’s `sdf_helper`
> conventions. For example, `Electric Field/Ex` has been updated to
> `Electric_Field_Ex`.

## Installation

Until this is on PyPI, please install directly from this repo:

```bash
pip install git+https://github.com/PlasmaFAIR/sdf-xarray.git@main
```

or from a local checkout:

```bash
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

print(df["Electric_Field_Ex"])

# <xarray.DataArray 'Electric_Field_Ex' (X_x_px_deltaf_electron_beam: 16)> Size: 128B
# [16 values with dtype=float64]
# Coordinates:
#   * X_x_px_deltaf_electron_beam  (X_x_px_deltaf_electron_beam) float64 128B 1...
# Attributes:
#     units:    V/m
#     full_name: "Electric Field/Ex"
```

### Multi file loading

```python
ds = xr.open_mfdataset(
    "*.sdf",
    data_vars='minimal', 
    coords='minimal', 
    compat='override', 
    preprocess=SDFPreprocess()
)

print(ds)

# Dimensions:
# time: 301, X_Grid_mid: 128, Y_Grid_mid: 128, Px_px_py_Photon: 200, Py_px_py_Photon: 200, X_Grid: 129, Y_Grid: 129, Px_px_py_Photon_mid: 199, Py_px_py_Photon_mid: 199
# Coordinates: (9)
# Data variables: (18)
# Indexes: (9)
# Attributes: (22)
```

### Loading SDF files directly

```python
from sdf_xarray import SDFFile

sdf_file = SDFFile("0010.sdf")

print(sdf_file.variables["Electric Field/Ex"])
# Variable(_id='ex', name='Electric Field/Ex', dtype=dtype('float64'), shape=(1024,), is_point_data=False, sdffile=<sdf_xarray.sdf_interface.SDFFile object at 0x10be7ebc0>, units='V/m', mult=1.0, grid='grid', grid_mid='grid_mid')

print(sdf_file.variables["Electric Field/Ex"].data)
# [ 0.00000000e+00  0.00000000e+00  0.00000000e+00 ... -4.44992788e+12  1.91704994e+13  0.00000000e+00]
```

### Reading particle data

By default, particle data isn't kept. Pass `keep_particles=True` as a
keyword argument to `open_dataset` (for single files) or
`open_mfdataset` (for multiple files):

```python
df = xr.open_dataset("0010.sdf", keep_particles=True)
```
