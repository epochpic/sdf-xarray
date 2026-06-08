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
  - name: University of York, United Kingdom
    index: 1
    ror: 04m01e293
date: 3 June 2026
bibliography: paper.bib
---

# Summary

sdf-xarray is a Python package that reads output files from the particle-in-cell code EPOCH into structured N-D labelled datasets provided by Xarray. Once loaded, these datasets can be interactively explored, animations can be generated, and variables can be converted between units.

# Statement of need

EPOCH [@arber:2015], developed at the University of Warwick, is a Fortran-based Particle-In-Cell (PIC) code widely used in laser-plasma physics, primarily within the United Kingdom. The code was first developed in early 2008, prior to the standardisation of many modern output file formats and as a result EPOCH uses the University of Warwicks' custom Self-Describing Format (SDF) binary files. 

Creating a new output module for the code to use a modern format such as netCDF [@rew:1989] is cumbersome as the code supports running simulations in 1D, 2D, 3D, or using a hybrid approximation or cylindrical geometry. All of these implementations are separate code repositories that contain diverging commit history making a unified module for all of them difficult.

# State of field

Several SDF wrappers have been created over the years including, but not limited to VisIt, Matlab, OpenPMD and a custom Python package called [`sdf_helper`](https://epochpic.github.io/documentation/visualising_output.html). While many of these visualisation software libraries are still very popular today they all come with downsides such as closed-source, paid licenses and age. 

The majority of current physicists are primarily familiar with Python and Matplotlib [@hunter:2007] for performing analysis of simulations. While `sdf_helper` might seem like an enticing choice it only has basic plotting routines, hasn't been actively maintained for several years and has no way to concatenate SDF files over time. Past versions of this package required installation via a Makefile located within the SDF-C library that wasn't compatible with many modern Python workflows, however it has recently been made avaialable on PyPI. By using Xarray [@hoyer:2017] to load SDF files we can take advantage of several features:

- Lazy loading which only loads in pointers to the data instead of the entire dataset, alleviating the RAM requirements for large SDF files.
- Built-in plotting functionality with Matplotlib.
- Conversion of datasets to NumPy [@harris:2020] or Pandas [@mckinney:2010].
- Opening multi-file datasets.

Another feature of sdf-xarray is that it has a vast, interactive series of [documentation](https://sdf-xarray.readthedocs.io/en/stable) pages built to be accessible for Physicists whereas `sdf_helper` only contains a basic single [documentation](https://epochpic.github.io/documentation/visualising_output/python_sdf_helper.html) page.

# Software design

sdf-xarray can be separated into two key sections; loading and animating. 

## Loading SDF files

The loading of an SDF file can be split into 3 steps:

1. The [`SDF-C`](https://github.com/epochpic/SDF_C) C-library reads the raw binary file.
1. Cython [@behnel:2010] then decodes the `header`, `run_info` and assigns the data into Python `dataclasses`.
1. These `dataclasses` are subsequently converted into a [custom backend](https://docs.xarray.dev/en/latest/internals/how-to-add-new-backend.html) suitable for use with the Xarray library.
  - Some of the SDF file's grids and variables are not loaded due to them being problematic and not used in practice. 
  - Grid and variable names contain slashes between each section and sometimes spaces; These are replaced with underscores to match the Pythonic snake_case. e.g. `"Derived/Number Density/Electron"` -> `"Derived_Number_Density_Electron"`. 
  - By default particle data is not loaded due to it needing to load $> 10^15$ particles per species leading to much higher RAM requirements.
  - The `input.deck` (simulation setup file) is appended to the global attributes.

Loading multiple files at once adds a time dimension and coordinate to the dataset using the `time` attribute from each SDF file and appends each SDF files data to it. At this stage we also check that the SDF files have the same `jobid` in case the user attempts to combine SDF files from two independent simulations.

One of the shortcomings of using Xarray is that it requires that all the data is stored on fixed grids. EPOCH outputs SDF files that can contain data that uses a global grid (i.e. number density) and data that produces a different grid every time an SDF file is output (i.e. particles, probes). The reason for this is that that particle order in EPOCH is not conserved. Even if you assign a particle-ID grid for particle data, particle `1` in `0000.sdf` may not be the same as particle `1` in `0001.sdf`.

## Animations

# Research impact statement

This library was originally developed for the machine learning pipeline toolkit [BEAM](https://github.com/epochpic/sdf-xarray#broad-epoch-analysis-modules-beam). The initial release of this package was developed by Peter Hill and has since been maintained and worked upon by Joel Adams. Since it's inception in 2024 several other EPOCH users at the York Plasma Institute have also used the library and consequently developed new features, or been the inspiration for the animation functions, unit conversion, and `input.deck` loading into a Python dictionary. 

This library has impacted the majority of EPOCH users at the University of York, and is used as teaching materials for a course on PIC code usage to undergraduate students. The library was also used in the EPOCH 2025 and 2026 workshops as the primary interfacing tool and has since seen usage across several other research institutions including Strathclyde University and Queens University Belfast. It has also seen usage in private companies such as First Light Fusion and several government entities.

# Benchmark

Discuss CPython parser from `SDF-C` to Xarray backend?

sdf_helper vs sdf-xarray time to open file in seconds and RAM usage

# AI usage disclosure

Some of the code and documentation in this library was partially developed with assistance from the GPT models by Google's Gemini, Anthropic's Claude and OpenAI's ChatGPT. The majority of the codebase was developed by humans and all generated code was verified by several developers prior to release.

# Acknowledgements

This projects initial development was funded by the PlasmaFAIR project, EPSRC Grant EP/V051822/1

We acknowledge the University of Warwick EPOCH development team for their support of the project and indirect contributions to this project by several anonymous contributors.

# References
