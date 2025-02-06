# sdf-xarray

![PyPI](https://img.shields.io/pypi/v/sdf-xarray?color=blue)
![Build/Publish](https://github.com/PlasmaFAIR/sdf-xarray/actions/workflows/build_publish.yml/badge.svg)
![Tests](https://github.com/PlasmaFAIR/sdf-xarray/actions/workflows/tests.yml/badge.svg)

sdf-xarray provides a backend for [xarray](https://xarray.dev) to read SDF files as created by
[EPOCH](https://epochpic.github.io) using the [SDF-C](https://github.com/Warwick-Plasma/SDF_C) library.
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
git clone https://github.com/PlasmaFAIR/sdf-xarray.git
cd sdf-xarray
pip install .
```

We recommend switching to [uv](https://docs.astral.sh/uv/) to manage packages.

## Usage

See documentation: <https://sdf-xarray.readthedocs.io/>

## Citing

If sdf-xarray contributes to a project that leads to publication, please acknowledge this by citing sdf-xarray. This can be done by clicking the "cite this repository" button located near the top right of this page.

## Broad EPOCH Analysis Modules (BEAM)

![BEAM logo](./BEAM.png)

BEAM is structured as a set of independent yet complementary open-source tools designed for analysing [EPOCH](https://epochpic.github.io/) simulations where researchers can adopt only the components they need, without being constrained by a rigid framework. The packages are as follows:

- [sdf-xarray](https://github.com/PlasmaFAIR/sdf-xarray): Reading and processing SDF files and converting them to [xarray](https://docs.xarray.dev/en/stable/).
- [epydeck](https://github.com/PlasmaFAIR/epydeck): Input deck reader and writer.
- [epyscan](https://github.com/PlasmaFAIR/epyscan): Create campaigns over a given parameter space using various sampling methods.
