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

```python
import xarray as xr

df = xr.open_dataset("0010.sdf")

print(df["Electric Field/Ex"])

# <xarray.DataArray 'Electric Field/Ex' (X_x_px_deltaf/electron_beam: 16)> Size: 128B
# [16 values with dtype=float64]
# Coordinates:
#   * X_x_px_deltaf/electron_beam  (X_x_px_deltaf/electron_beam) float64 128B 1...
# Attributes:
#     units:    V/m
```
