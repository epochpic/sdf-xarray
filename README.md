# sdf-xarray

![PyPI](https://img.shields.io/pypi/v/sdf-xarray?color=blue)
![Build/Publish](https://github.com/PlasmaFAIR/sdf-xarray/actions/workflows/build_publish.yml/badge.svg)
![Tests](https://github.com/PlasmaFAIR/sdf-xarray/actions/workflows/tests.yml/badge.svg)

`sdf-xarray` provides a backend for [xarray](https://xarray.dev) to
read SDF files as created by the [EPOCH](https://epochpic.github.io)
plasma PIC code. It also uses the [SDF-C](https://github.com/Warwick-Plasma/SDF_C) library.

## Installation

Install from PyPI with:

```bash
pip install sdf-xarray
```

> [!NOTE]
> For use within jupyter notebooks, run this additional command after installation:
>
> ```bash
> pip install "sdf-xarray[jupyter]"
> ```

or from a local checkout:

```bash
git clone https://github.com/PlasmaFAIR/sdf-xarray.git
cd sdf-xarray
pip install .
```

We recommend switching to [uv](https://docs.astral.sh/uv/) to manage packages.

## Usage

`sdf-xarray` is a backend for xarray, and so is usable directly from
xarray:

### Single file loading

```python
import xarray as xr

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

To open a whole simulation at once, pass `preprocess=sdf_xarray.SDFPreprocess()`
to `xarray.open_mfdataset`:

```python
import xarray as xr
from sdf_xarray import SDFPreprocess

with xr.open_mfdataset("*.sdf", preprocess=SDFPreprocess()) as ds:
    print(ds)

# Dimensions:
# time: 301, X_Grid_mid: 128, ...
# Coordinates: (9) ...
# Data variables: (18) ...
# Indexes: (9) ...
# Attributes: (22) ...
```

`SDFPreprocess` checks that all the files are from the same simulation, as
ensures there's a `time` dimension so the files are correctly concatenated.

If your simulation has multiple `output` blocks so that not all variables are
output at every time step, then those variables will have `NaN` values at the
corresponding time points.

Alternatively, we can create a separate time dimensions for each `output` block
(essentially) using `sdf_xarray.open_mfdataset` with `separate_times=True`:

```python
from sdf_xarray import open_mfdataset

with open_mfdataset("*.sdf", separate_times=True) as ds:
    print(ds)

# Dimensions:
# time0: 301, time1: 31, time2: 61, X_Grid_mid: 128, ...
# Coordinates: (12) ...
# Data variables: (18) ...
# Indexes: (9) ...
# Attributes: (22) ...
```

This is better for memory consumption, at the cost of perhaps slightly less
friendly comparisons between variables on different time coordinates.

### Reading particle data

By default, particle data isn't kept as it takes up a lot of space. Pass
`keep_particles=True` as a keyword argument to `open_dataset` (for single files)
or `open_mfdataset` (for multiple files):

```python
df = xr.open_dataset("0010.sdf", keep_particles=True)
```

### Loading SDF files directly

For debugging, sometimes it's useful to see the raw SDF files:

```python
from sdf_xarray import SDFFile

with SDFFile("0010.sdf") as sdf_file:
    print(sdf_file.variables["Electric Field/Ex"])

    # Variable(_id='ex', name='Electric Field/Ex', dtype=dtype('float64'), ...

    print(sdf_file.variables["Electric Field/Ex"].data)

    # [ 0.00000000e+00  0.00000000e+00  0.00000000e+00 ... -4.44992788e+12  1.91704994e+13  0.00000000e+00]
```
