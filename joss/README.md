# JOSS Submission

This directory contains the paper and scripts for the submission to the Journal of Open Source Software

- `paper.md`: Paper
- `paper.bib`: bibliography
- `generate_figures.py`: Generate the figures for the plot
- `input.deck`: The EPOCH setup script used to generate the data for the figures
- `Electric_Field_Ey.png`: A plot of a laser focusing in a vacuum of the 10th SDF file
- `Electric_Field_Ey.gif`: The animation of a laser focusing in a vacuum
- `Electric_Field_Ey_frames.png`: 4 plots of a laser focusing in a vacuum used in place of the GIF for the paper

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