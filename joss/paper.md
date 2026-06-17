---
title: 'sdf-xarray: Interactive data reading for particle-in-cell simulations'
tags:
  - Python
  - xarray
  - EPOCH
  - PIC
  - interactivity
  - data
authors:
  - name: Joel Luca Adams
    orcid: 0009-0005-4889-5231
    equal-contrib: true
    corresponding: true
    affiliation: 1
  - name: Peter Hill
    orcid: 0000-0003-3092-1858
    equal-contrib: true
    affiliation: 1
  - name: Liam Pattinson
    orcid: 0000-0001-8604-6904
    affiliation: 1
  - name: Shaun Doherty
    orcid: 0009-0005-0693-030X
    affiliation: 1
  - name: Sviatoslav Shekhanov
    orcid: 0000-0002-2125-8962
    affiliation: 1
  - name: Chris Herdman
    orcid: 0000-0002-5159-0130
    affiliation: 1
  - name: Lawrence Dior
    orcid: 0000-0003-4138-4576
    affiliation: 1
affiliations:
  - name: York Plasma Institute, University of York, United Kingdom
    index: 1
    ror: 04m01e293
date: 3 June 2026
bibliography: paper.bib
---

# Summary

EPOCH is a plasma physics code that outputs files using a custom binary format called SDF. `sdf-xarray` is a Python package which reads these files and parses them it into structured N-D labelled datasets provided by `Xarray`. `sdf-xarray` has built-in functions for plotting, animation and unit conversion, allowing for simple interaction and manipulation for easy data analysis.

# Statement of need

EPOCH [@arber:2015], developed at the University of Warwick, is a Fortran-based Particle-In-Cell (PIC) code widely used in laser-plasma physics, primarily within the United Kingdom. The code was first developed at the University of Warwick in early 2008, prior to the standardisation of many modern output file formats and as a result uses the universities' custom Self-Describing Format (SDF) binary files. 

Integrating a modern output module like `NetCDF` [@rew:1989] is challenging because the codebase accommodates one-, two-, and three-dimensional simulations across three variants: a regular grid geometry, a cylindrical geometry and a hybrid approximation. Multiple copies of the variants exists and are stored in forks and branches containing diverging commit histories making development of a unified module challenging.

# State of field

Several SDF wrappers [@bennett:2014a] for use in visualisation software have been created over the years including, but not limited to (i) `VisIt` [@childs:2012], (ii) `Matlab` [@matlab:2022] which is closed-source and requires a paid license, (iii) `OpenPMD` [@huebl:2015] which is not currently widely adopted and (iv) a custom Python package called `sdf_helper`.

Python and `Matplotlib` [@hunter:2007] are standard tools for plasma physics simulation analysis. The `sdf_helper` Python package supports this workflow by providing simple data extraction to `NumPy` [@harris:2020] and custom `Matplotlib` plotting routines. Unfortunately, it lacks native capabilities for concatenating multiple SDF files into time-resolved datasets.

Developed as a modern successor to `sdf_helper`, `sdf-xarray` converts SDF files to `Xarray` [@hoyer:2017] datasets, enabling users to leverage core ecosystem features, including:

- **Lazy data loading via `Dask` [@matthew:2015]:** Instantiates pointers rather than loading the entire dataset into memory, substantially mitigating RAM constraints when handling large-scale files on the order of 10-100 GB.
- **Deferred computation:** Leverages `Dask` to postpone execution on data arrays until explicitly required or evaluated.
- **Ecosystem interoperability:** Simplifies conversion of dataset arrays to `NumPy` or `Pandas` [@mckinney:2010] structures for downstream analysis.
- **Interactive development:** Provides native compatibility with `Jupyter` notebooks [@granger:2021] to support iterative workflows.
- **Built-in visualisation:** Contains integrated `Matplotlib` routines for rapid, native plotting of multidimensional data.
- **Multi-file aggregation:** Facilitates the simultaneous opening and unified handling of split-file datasets.

In addition to leveraging `Xarray`'s core ecosystem, `sdf-xarray` has comprehensive [documentation](https://sdf-xarray.readthedocs.io/en/stable) which is actively maintained and makes use of `Jupyter` notebooks to illustrate the interactive nature of the package.

Both `sdf_helper` and `sdf-xarray` serve as wrappers around the C-based `SDF-C` library [@bennett:2014b]. Although the underlying library historically required manual compilation via a Makefile, `sdf-xarray` utilises the modern `scikit-build-core` backend to automate this process for local builds. Furthermore, during the release cycle, `sdf-xarray` leverages `cibuildwheel` to distribute pre-compiled binaries across Windows, MacOS, and various Linux distributions. Originally, `sdf_helper`, released back in 2014, did not have this automated build process, making installation less consistent across operating systems. It also did not respect isolated Python virtual environments, causing some users to face system-wide dependency conflicts. Several months after the release of `sdf-xarray` in 2024, `sdf_helper` was updated to adopt a similar automated pipeline and published on PyPI as `sdfr` to alleviate these deployment challenges.

# Software design

This packages design can be separated into three key sections; loading, plotting and rescaling. 

## Loading SDF files

The loading of an SDF file can be split into 3 steps:

1. The `SDF-C` C library reads the raw binary file.
1. `Cython` [@behnel:2010] then decodes the `header`, `run_info` and converts the data into Python `dataclasses`.
1. These `dataclasses` are subsequently parsed into a [custom backend](https://docs.xarray.dev/en/latest/internals/how-to-add-new-backend.html) suitable for use with the `Xarray` library.
    - Some of the file's grids and variables are not loaded due to them being problematic and not used in practice. 
    - Grid and variable names contain slashes between each section and sometimes spaces; These are replaced with underscores to match the Pythonic snake case. e.g. `"Derived/Number Density/Electron"` -> `"Derived_Number_Density_Electron"`. 
    - Particle data takes up a significant portion of the size of a file if it is present and therefore by default is not loaded to alleviate the RAM requirements.
    - The `input.deck` (simulation setup file) is appended to the datasets' global attributes via `epydeck` [@hill:2024].

loading multiple files introduces a time dimension and coordinate derived from each file's `time` attribute, appending the dataset's data along this axis. At this stage we also check that the files have the same `jobid` in case the user attempts to combine files from two different simulations.

A primary limitation of `Xarray` is its strict requirement for fixed grids. EPOCH outputs both fixed global-grid data and variable-grid data that can change with each SDF output; consequently, datasets with time-varying grid sizes cannot be natively integrated into standard `Xarray` structures. To mitigate this constraint, `sdf-xarray` provides a `separate_times` flag when opening multi-file datasets, which creates distinct time dimensions for variables with differing output frequencies. This approach increases RAM overhead as the dimension sizes of each variable must be explicitly evaluated prior to a being assigned to a time dimension.

## Rescaling datasets

EPOCH outputs all data in base International System (SI) units. It can be convenient to convert these units when handling coordinate data; to that end a custom function was developed and an example can be found below:

```python
# Convert the time to femtoseconds
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
# Convert the x and y coords to microns
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])
```

This is often used in conjunction with generating plots and animations.

Converting variables can also be done by either directly manipulating the underlying `NumPy` array or using the `Pint` [@grecco:2012] package along with the `Xarray` API `pint-xarray` [@magin:2020].

## Plotting

`Xarray` provides a simple interface for plotting variables using `Matplotlib`. An example of which is:

```python
import sdf_xarray as sdfxr

# Opens a single-file dataset
ds = sdfxr.open_dataset("0010.sdf")
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])

ds["Electric_Field_Ey"].epoch.plot()
```

![Plot of the electric field of a laser focusing in a vacuum, generated through `sdf-xarray`.](Electric_Field_Ey.png){width="60%"}

### Animations

Building animations provides insight into how systems evolving over time. While `Matplotlib` allows users to build animations, it can require quite a complicated setup in order to work with `Xarray`. As a result, `sdf-xarray` contains a custom function that builds on top of `Matplotlib`'s implementation and provides a simple user interface. An example animation of a dataset variable evolving over time is as follows:

```python
import sdf_xarray as sdfxr

# Opens a multi-file dataset using globs or a list of paths
ds = sdfxr.open_mfdataset("*.sdf")
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])

anim = ds["Electric_Field_Ey"].epoch.animate()
```

![Frames from an animation of the electric field of a laser focusing in a vacuum, generated through `sdf-xarray`.](Electric_Field_Ey_frames.png)

The minimum and maximum values of a variable can change between each SDF file, so when generating an animation the limits must be found over the whole dataset. This behaviour exists by default in `sdf-xarray` animations.

EPOCH allows users to create simulations in which axes shift throughout the simulation (i.e. to track a lasers propagation through a long block of plasma) called moving windows as simulating the full picture is computationally expensive. `sdf-xarray` animations allow the user to specify a boolean value for this `moving_window` functionality to follow the simulation box instead of maintaining fixed axes.

On top of building single variable animations, users can utilise the `animate_multiple()` function to overlay multiple variables.

Further examples and explanation of animations can be seen in the [documentation](https://sdf-xarray.readthedocs.io/en/stable/animation.html).

# Research impact statement

This library was originally developed for the machine learning pipeline toolkit [BEAM](https://github.com/epochpic/sdf-xarray#broad-epoch-analysis-modules-beam). The initial release of this package was developed by Peter Hill and has since been maintained and iterated upon by Joel Adams and several others. Since it's inception in 2024, many EPOCH users at the York Plasma Institute have adopted the library for their research and consequently developed new features. 

On top of it's adoption by researchers at the University of York, Strathclyde University, Queens University Belfast, First Light Fusion and a few government entities, it is also being used in teaching materials for a course on PIC codes delivered to undergraduate students. The library was also used as the primary interfacing tool in the EPOCH 2025 and 2026 workshops.

# AI usage disclosure

Some of the code and documentation in this library was partially developed with assistance from the GPT models by Google's Gemini, Anthropic's Claude and OpenAI's ChatGPT. The majority of the codebase was developed by humans and all generated code was verified by several developers prior to release.

# Acknowledgements

This projects initial development was funded by the PlasmaFAIR project, EPSRC Grant EP/V051822/1

We acknowledge the University of Warwick EPOCH development team for their support of the project and indirect contributions to this project by several anonymous contributors.

# References
