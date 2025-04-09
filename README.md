# sdf-xarray

![PyPI](https://img.shields.io/pypi/v/sdf-xarray?color=blue)
![Build/Publish](https://github.com/epochpic/sdf-xarray/actions/workflows/build_publish.yml/badge.svg)
![Tests](https://github.com/epochpic/sdf-xarray/actions/workflows/tests.yml/badge.svg)

sdf-xarray provides a backend for [xarray](https://xarray.dev) to read SDF files as created by
[EPOCH](https://epochpic.github.io) using the [SDF-C](https://github.com/epochpic/SDF_C) library.
Part of [BEAM](#broad-epoch-analysis-modules-beam) (Broad EPOCH Analysis Modules).

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
git clone https://github.com/epochpic/sdf-xarray.git
cd sdf-xarray
pip install .
```

We recommend switching to [uv](https://docs.astral.sh/uv/) to manage packages.

## Usage

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

### Multi-file loading

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

For more in depth documentation please visit: <https://sdf-xarray.readthedocs.io/>

## Citing

If sdf-xarray contributes to a project that leads to publication, please acknowledge this by citing sdf-xarray. This can be done by clicking the "cite this repository" button located near the top right of this page.

## Broad EPOCH Analysis Modules (BEAM)

![BEAM logo](./BEAM.png)

In line with the FAIR principles—Findable, Accessible, Interoperable, and Reusable—each package is openly published with clear documentation and versioning (Findable), distributed via public repositories (Accessible), designed to follow common standards for data structures and interfaces (Interoperable), and includes licensing and metadata to support long-term use and adaptation (Reusable). The packages are as follows:

- [sdf-xarray](https://github.com/epochpic/sdf-xarray): Reading and processing SDF files and converting them to [xarray](https://docs.xarray.dev/en/stable/).
- [epydeck](https://github.com/epochpic/epydeck): Input deck reader and writer.
- [epyscan](https://github.com/epochpic/epyscan): Create campaigns over a given parameter space using various sampling methods.

## PlasmaFAIR

![PlasmaFAIR logo](PlasmaFAIR.svg)

Originally developed by [PlasmaFAIR](https://plasmafair.github.io), EPSRC Grant EP/V051822/1