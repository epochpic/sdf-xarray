# JOSS Submission

This directory contains the paper and scripts for the submission to the Journal of Open Source Software

- `paper.md`: Paper
- `paper.bib`: bibliography
- `generate_figures.py`: Generate the figures for the plot
- `input.deck`: The EPOCH setup script used to generate the data for the figures
- `Electric_Field_Ey.png`: A plot of a laser focusing in a vacuum of the 10th SDF file
- `Electric_Field_Ey.gif`: The animation of a laser focusing in a vacuum
- `Electric_Field_Ey_frames.png`: 4 plots of a laser focusing in a vacuum used in place of the GIF for the paper
- `benchmark.py`: Runs EPOCH to create SDF files, then measures the time and peak memory needed by `sdf-xarray` and `sdf_helper` to open single files of increasing size, and to take a lineout through a time series of an increasing number of files. Run with `uv run benchmark.py path/to/epoch/epoch2d/bin/epoch2d` (needs EPOCH compiled, see below)
- `benchmark.png`: Time and memory to open a single SDF file, created by `benchmark.py`
- `benchmark_time_series.png`: Time and memory to take a lineout through a time series, created by `benchmark.py`

## Compiling and running EPOCH

1. `git clone --recursive https://github.com/epochpic/epoch.git`
2. Install libraries
	1. (ON MAC) `brew install open-mpi`
	2. (LINUX) `sudo apt install gfortran openmpi-bin openmpi-common libopenmpi-dev libgtk2.0-dev`
3. Open the `epoch2d` folder
4. Compile the executable `make COMPILER=gfortran MPIF90=mpif90 -j4`
5. Run the simulation `mpirun -n 8 ./bin/epoch2d <<< sdf-xarray/joss`

## Building the JOSS PDF

`pandoc paper.md --citeproc --to=pdf -o paper.pdf`