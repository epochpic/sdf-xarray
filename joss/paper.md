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

sdf-xarray is a Python package that reads output files from the particle-in-cell code EPOCH into structured N-D labelled datasets provided by Xarray. Once loaded, these datasets can be interactively explored, animations can be generated, and variables can be converted between units.

# Statement of need

EPOCH [@arber:2015], developed at the University of Warwick, is a Fortran-based Particle-In-Cell (PIC) code widely used in laser-plasma physics, primarily within the United Kingdom. The code was first developed at the University of Warwick in early 2008, prior to the standardisation of many modern output file formats and as a result uses the Universities custom Self-Describing Format (SDF) binary files. 

Creating a new output module for the code to use a modern format such as netCDF [@rew:1989] is cumbersome as the code supports running simulations in 1D, 2D, 3D, using a hybrid approximation or cylindrical geometry. All of these implementations are separate code repositories that contain diverging commit histories which makes developing a unified module difficult.

# State of field

Several SDF wrappers for use in visualisation software have been created over the years including, but not limited to VisIt [@childs:2012], Matlab [@matlab:2022], OpenPMD [@huebl:2015] and a custom Python package called [`sdf_helper`](https://epochpic.github.io/documentation/visualising_output.html). While many of these visualisation software libraries are still very popular today they all come with downsides such as closed-source, paid licenses and lack of recent development. 

The majority of current physicists are primarily familiar with Python and Matplotlib [@hunter:2007] for performing analysis of simulations. While `sdf_helper` might seem like an enticing choice at first it only has basic Matplotlib plotting routines, hasn't been actively maintained for several years and has no ability to concatenate SDF files over time. Past versions of this package required installation via a Makefile located within the [`SDF-C`](https://github.com/epochpic/SDF_C) library that wasn't compatible with many modern Python workflows, however it has recently been made avaialable on PyPI under the name `sdfr`. 

To address the above issues with `sdf_helper` this library was developed which converts the SDF files into Xarray [@hoyer:2017] datasets. By loading SDF files using this library we can take advantage of several features provided by it:

- Lazy loading using Dask [@matthew:2015] which only loads in pointers to the data instead of the entire dataset, alleviating the RAM requirements for large SDF files.
- Conversion of dataset arrays to NumPy [@harris:2020] or Pandas [@mckinney:2010].
- Built-in interactivity with Jupyter notebooks [@granger:2021].
- Built-in plotting functionality with Matplotlib.
- Opening multi-file datasets.

Another feature of sdf-xarray is that it has a vast, interactive (using Jupyter notebooks) series of [documentation](https://sdf-xarray.readthedocs.io/en/stable) pages whereas `sdf_helper` only contains a single [documentation](https://epochpic.github.io/documentation/visualising_output/python_sdf_helper.html) page.

# Software design

This packages design can be separated into three key sections; loading, animating and rescaling. 

## Loading SDF files

The loading of an SDF file can be split into 3 steps:

1. The `SDF-C` C-library reads the raw binary file.
1. Cython [@behnel:2010] then decodes the `header`, `run_info` and converts the data into Python `dataclasses`.
1. These `dataclasses` are subsequently parsed into a [custom backend](https://docs.xarray.dev/en/latest/internals/how-to-add-new-backend.html) suitable for use with the Xarray library.
  - Some of the SDF file's grids and variables are not loaded due to them being problematic and not used in practice. 
  - Grid and variable names contain slashes between each section and sometimes spaces; These are replaced with underscores to match the Pythonic snake case. e.g. `"Derived/Number Density/Electron"` -> `"Derived_Number_Density_Electron"`. 
  - By default particle data is not loaded due to it needing to load several orders of magnitudes of particles per species leading to much higher RAM requirements.
  - The `input.deck` (simulation setup file) is appended to the datasets' global attributes via epydeck [@hill:2024].

Loading multiple files at once adds a time dimension and coordinate to the dataset using the `time` attribute from each SDF file and appends each SDF files data to it. At this stage we also check that the SDF files have the same `jobid` in case the user attempts to combine SDF files from two independent simulations.

One of the shortcomings of using Xarray is that it requires that all the data is stored on fixed grids. EPOCH outputs SDF files that can contain data that uses a global grid (i.e. number density) and data that produces a different grid every time an SDF file is output (i.e. particles, probes). The reason for this is that that particle order in EPOCH is not conserved. Even if you assign a particle-ID grid for particle data, particle `1` in `0000.sdf` may not be the same as particle `1` in `0001.sdf`.

## Animations

Building animations of systems evolving over time (or some other coordinate) has always been helpful in providing insight to both the user and for use in presentations. While Matplotlib allows users to build animations, it can require quite a complicated setup in order to work with Xarray. As a result, sdf-xarray contains a custom function that builds on top of Matplotlib's implementation and provides a simple user interface. An example animation of a dataset variable evolving over time is as follows:

```python
import sdf_xarray as sdfxr

ds = sdfxr.open_mfdataset("path/to/dataset/*.sdf")
anim = ds["Derived_Number_Density"].epoch.animate()
anim.show() # Visualisation directly in a Jupyter notebook
anim.save("number_density.mp4", fps=10) # Or save the animation
```

When creating animations of 2D simulation data a colorbar is required so to avoid it jumping around between frames, its min and max values are calculated at the start so that the final animation includes a fixed colorbar. 

EPOCH allows users to create simulations in which axes shift throughout the simulation (i.e. to track a lasers propagation through a long block of plasma) called moving windows as simulating the full picture is computationally expensive. This behaviour is supported in sdf-xarray animations, so if a user loads a dataset where there are `NaN`s in the data it interprets it as a moving window and changes the corresponding axes throughout the animation.

On top of building single variable animations, users can utilise the `animate_multiple()` function to overlay multiple variables (i.e. 1D animation of electron density vs ion density over time).

Further examples and explanation of animations can be seen in the [documentation](https://sdf-xarray.readthedocs.io/en/stable/animation.html).

## Rescaling datasets

Most EPOCH users tend to simulate plasma with a physical size on the order of $\sim 10^{-6}$ (microns) metres with a simulated time on the order of $\sim 10^{-15}$ (femto) seconds. As a result of this, a custom function for rescaling the physical size and time dimensions was developed. An example of rescaling both of these dimensions is as follows:

```python
# Convert the time to femtoseconds
ds = ds.epoch.rescale_coords(1e15, "fs", "time")
# Convert the x and y coords to microns
ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid"])
```

This is often used in conjunction with the animation function in order to produce visually cleaner animations.

Converting variables can also be done by either directly manipulating the underlying NumPy array or using the [Pint](https://github.com/hgrecco/pint) package along with the Xarray API [pint-xarray](https://github.com/xarray-contrib/pint-xarray).

# Research impact statement

This library was originally developed for the machine learning pipeline toolkit [BEAM](https://github.com/epochpic/sdf-xarray#broad-epoch-analysis-modules-beam). The initial release of this package was developed by Peter Hill and has since been maintained and iterated upon by Joel Adams and several others. Since it's inception in 2024, many EPOCH users at the York Plasma Institute have adopted the library for their research and consequently developed new features. 

On top of it's adoption by PhD Students and academics at the University of York, it is also being used in teaching materials for a course on PIC codes delivered to undergraduate students. The library was also used as the primary interfacing tool in the EPOCH 2025 and 2026 workshops. It has also seen use across several other research institutions including Strathclyde University, Queens University Belfast, First Light Fusion and a few government entities.

# AI usage disclosure

Some of the code and documentation in this library was partially developed with assistance from the GPT models by Google's Gemini, Anthropic's Claude and OpenAI's ChatGPT. The majority of the codebase was developed by humans and all generated code was verified by several developers prior to release.

# Acknowledgements

This projects initial development was funded by the PlasmaFAIR project, EPSRC Grant EP/V051822/1

We acknowledge the University of Warwick EPOCH development team for their support of the project and indirect contributions to this project by several anonymous contributors.

# References
