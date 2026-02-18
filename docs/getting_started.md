# Getting Started

## Installation

```{important}
To install this package, ensure that you are using one of the supported Python
versions [![Supported Python versions](https://img.shields.io/pypi/pyversions/sdf-xarray.svg)](https://github.com/epochpic/sdf-xarray)
```

Install sdf-xarray from PyPI with:

```bash
pip install sdf-xarray
```

or download this code locally:

```bash
git clone --recursive https://github.com/epochpic/sdf-xarray.git
cd sdf-xarray
pip install .
```

## Interaction

There are two main ways to load EPOCH SDF files into xarray objects: using the dedicated
<project:#sdf_xarray> functions or using the standard <inv:#xarray> interface with our custom engine.
For examples of how to use these functions see [](./key_functionality.md#loading-sdf-files).

All code examples throughout this documentation are visualised using Jupyter notebooks
so that you can interactively explore the datasets. To do this on your machine make
sure that you have the necessary dependencies installed:

```bash
pip install "sdf-xarray[jupyter]"
```

```{important}
When loading SDF files, variables related to `boundaries`, `cpu` and `output file`
are excluded as they are problematic. If you wish to load these variables in see
[](./key_functionality.md#loading-raw-files).
```

### Using sdf_xarray (Recommended)

These functions are wrappers designed specifically for SDF data, providing the most
straightforward experience:

- **Single files**: Use <project:#sdf_xarray.open_dataset> or <project:#sdf_xarray.open_datatree>
- **Multiple files**: Use <project:#sdf_xarray.open_mfdataset> or <project:#sdf_xarray.open_mfdatatree>
- **Raw files**: use <project:#sdf_xarray.sdf_interface.SDFFile>

### Using xarray

If you prefer using the native <inv:#xarray> functions, you can use the <inv:#xarray.open_dataset>,
<inv:#xarray.open_datatree> and <inv:#xarray.open_mfdataset>. Strangely there is no function in
<inv:#xarray> for `xarray.open_mfdatatree`.

These functions should all work out of the box as long as <project:#sdf_xarray> is installed on your
system, if you are having issues with it reading files, you might need to pass the parameter
`engine=sdf_engine` when calling any of the above xarray functions.
