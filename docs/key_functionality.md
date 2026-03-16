---
file_format: mystnb
kernelspec:
  name: python3
---

# Key Functionality

```{code-cell} ipython3
import xarray as xr
import sdf_xarray as sdfxr
import matplotlib.pyplot as plt
```

## Loading SDF files

### Loading single files

```{code-cell} ipython3
sdfxr.open_dataset("tutorial_dataset_1d/0010.sdf")
```

You can also load the data in as a <inv:#xarray.DataTree>, which organises the data
hierarchically into `groups` (for example grouping related quantities such as the individual
components of the electric and magnetic fields) while keeping each item as a <inv:#xarray.Dataset>.

```{code-cell} ipython3
sdfxr.open_datatree("tutorial_dataset_1d/0010.sdf")
```

(loading-raw-files)=

### Loading raw files

If you wish to load data directly from the `SDF.C` library and ignore
the <inv:#xarray> interface layer.

```{code-cell} ipython3
raw_ds = sdfxr.SDFFile("tutorial_dataset_1d/0010.sdf")
raw_ds.variables.keys()
```

### Loading multiple files

Multiple files can be loaded using one of two methods. The first of which
is by using the <project:#sdf_xarray.open_mfdataset>.

```{tip}
If your simulation includes multiple `output` blocks that specify different variables
for output at various time steps, variables not present at a specific step will default
to a nan value. To remove these nan values we suggest using the <inv:#xarray.DataArray.dropna>
function or following our implmentation in [](#loading-sparse-data).
```

```{code-cell} ipython3
sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")
```

Alternatively, files can be loaded using <inv:#xarray.open_mfdataset> however when loading in
all the files we have do some processing of the data so that we can correctly align it along
the time dimension; This is done via the `preprocess` parameter utilising the
<project:#sdf_xarray.SDFPreprocess> function.

```{code-cell} ipython3
xr.open_mfdataset(
   "tutorial_dataset_1d/*.sdf",
   join="outer",
   compat="no_conflicts",
   preprocess=sdfxr.SDFPreprocess()
)
```

You can also load the data in as a <inv:#xarray.DataTree>, which organises the data
hierarchically into `groups` (for example grouping related quantities such as the individual
components of the electric and magnetic fields) while keeping each item as a <inv:#xarray.Dataset>.

```{code-cell} ipython3
sdfxr.open_mfdatatree("tutorial_dataset_1d/*.sdf")
```

### Loading sparse data

When dealing with sparse data (where different variables are saved at different,
non-overlapping time steps) you can optimize memory usage by loading the data with
<project:#sdf_xarray.open_mfdataset> using the parameter `separate_times=True`. This
approach creates a distinct time dimension for each output block, avoiding the
need for a single, large time dimension that would be filled with nan values. This
significantly reduces memory consumption, though it requires more deliberate handling
if you need to compare variables that exist on these different time coordinates.

```{code-cell} ipython3
sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", separate_times=True)
```

### Loading particle data

```{warning}
It is **not recommended** to use <inv:#xarray.open_mfdataset> or
<project:#sdf_xarray.open_mfdataset> to load particle data from multiple
SDF outputs. The number of particles often varies between outputs,
which can lead to inconsistent array shapes that these functions
cannot handle. Instead, consider loading each file individually and
then concatenating them manually.
```

```{note}
When loading multiple probes from a single SDF file, you **must** use the
`probe_names` parameter to assign a unique name to each. For example,
use `probe_names=["Front_Electron_Probe", "Back_Electron_Probe"]`.
Failing to do so will result in dimension name conflicts.
```

By default, particle data isn't kept as it takes up a lot of space.
Pass `keep_particles=True` as a keyword argument to
<inv:#xarray.open_dataset> (for single files) or <inv:#xarray.open_mfdataset> (for
multiple files).

```{code-cell} ipython3
sdfxr.open_dataset("tutorial_dataset_1d/0010.sdf", keep_particles=True)
```

### Loading specific variables

When loading datasets containing several (`>10`) coordinates/dimensions
using <project:#sdf_xarray.open_mfdataset>, <inv:#xarray> may struggle to locate
the necessary RAM to concatenate all of the data (as seen in
[Issue #57](https://github.com/epochpic/sdf-xarray/issues/57)).
In this instance, you can optimize memory usage by loading only the data
you need using the keyword argument `data_vars` and passing one or more
variables. This creates a dataset consisting only of the given variable(s)
and the relevant coordinates/dimensions, significantly reducing memory
consumption.

```{code-cell} ipython3
sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", data_vars=["Electric_Field_Ex"])
```

(loading-input-deck)=

### Loading the input.deck

When loading SDF files, <project:#sdf_xarray> will attempt to automatically load
the `input.deck` file used to initialise the simulation from the same
directory as the SDF file. If the file is not found, it will silently fail
and continue loading the SDF file as normal. This file contains the initial
simulation setup information which is not present in SDF outputs. By loading
this file, you can access these parameters as part of your dataset's metadata.
To do this, use the `deck_path` parameter when loading an SDF file with
<project:#sdf_xarray.open_dataset>, <inv:#xarray.open_dataset>, <project:#sdf_xarray.open_datatree>,
<inv:#xarray.open_datatree>, <project:#sdf_xarray.open_mfdataset> or <project:#sdf_xarray.open_mfdatatree>.

There are a few ways you can load an input deck:

- **Default behaviour**: The input deck is loaded from the same directory
  as the SDF file if it exists. If it does not exist, it will silently fail.
- **Relative path**: (e.g. `"template.deck"`) Searches for that specific filename
  within the same directory as the SDF file.
- **Absolute path**: (e.g. `"/path/to/input.deck"`) Uses the full, specified path
  to locate the file.

An example of loading a deck can be seen below

```{code-cell} ipython3
:tags: [hide-output]

import json
from IPython.display import Code

ds = xr.open_dataset("tutorial_dataset_1d/0010.sdf")
# The results are accessible by calling
deck = ds.attrs["deck"]

# Some prettification to make it looks nice in jupyter notebooks
json_str = json.dumps(deck, indent=4)
Code(json_str, language='json')
```

## Data interaction examples

When loading in either a single dataset or a group of datasets you
can access the following methods to explore the dataset:

- `ds.variables` to list variables. (e.g. Electric Field, Magnetic
  Field, Particle Count)
- `ds.coords` for accessing coordinates/dimensions. (e.g. x-axis,
  y-axis, time)
- `ds.attrs` for metadata attached to the dataset. (e.g. filename,
  step, time)

It is important to note here that <inv:#xarray> lazily loads the data
meaning that it only explicitly loads the results your currently
looking at when you call `.values`

```{code-cell} ipython3
ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

ds["Electric_Field_Ex"]
```

On top of accessing variables, you can plot these datasets using
[`xarray.DataArray.epoch.plot`](project:#sdf_xarray.dataarray_accessor.EpochAccessor.plot).
This is a custom <project:#sdf-xarray> plotting routine that builds on top of
<inv:#xarray.DataArray.plot>, so you keep the familiar <inv:#xarray> plotting
behaviour while using <project:#sdf-xarray> conveniences (see 
[here](project:#sdf_xarray.dataarray_accessor.EpochAccessor.plot) for details).
Under the hood, plotting is still handled by <inv:#matplotlib>, which means you
can use the full <inv:#matplotlib> API to customise your figure.

```{code-cell} ipython3
# This is discretized in both space and time
ds["Electric_Field_Ex"].epoch.plot()
plt.title("Electric field along the x-axis")
plt.show()
```

When loading a multi-file dataset using <project:#sdf_xarray.open_mfdataset>, a
time dimension is automatically added to the resulting <inv:#xarray.Dataset>.
This dimension represents all the recorded simulation steps and allows
for easy indexing. To quickly determine the number of time steps available,
you can check the size of the time dimension.

```{code-cell} ipython3
# This corresponds to the number of individual SDF files loaded
print(f"There are a total of {ds['time'].size} time steps")

# You can look up the actual simulation time for any given index
sim_time = ds['time'].values[20]
print(f"The time at the 20th simulation step is {sim_time:.2e} s")
```

You can select and extract a single simulation snapshot using the integer
index of the time step with the <inv:#xarray.Dataset.isel> function. This can be
done by passsing the index to the `time` parameter (e.g., `time=0` for
the first snapshot).

```{code-cell} ipython3
ds["Electric_Field_Ex"].isel(time=20)
```

We can also use the <inv:#xarray.Dataset.sel> function if you wish to pass a
value intead of an index.

```{tip}
If you know roughly what time you wish to select but not the exact value
you can use the parameter `method="nearest"`.
```

```{code-cell} ipython3
ds["Electric_Field_Ex"].sel(time=sim_time)
```

## Visualisation on HPCs

In many cases you will be running EPOCH simulations via a HPC cluster and your
subsequent SDF files will probably be rather large and cumbersome to interact with
via traditional Jupyter notebooks. In some cases your HPC may outright block the
use of Jupyter notebooks entirely. To circumvent this issue you can use a Terminal
User Interface (TUI) which renders the contents of SDF files directly in a Terminal
and allows for you to do some simple data analysis and visualisation. To do this we
shall leverage the [xr-tui](https://github.com/samueljackson92/xr-tui) package
which can be installed to either a venv or globally using:

```bash
pipx install xr-tui sdf-xarray
```

or if you are using `uv`

```bash
uv tool install xr-tui --with sdf-xarray
```

Once installed you can visualise SDF files by simply writing in the command line

```bash
xr path/to/simulation/0000.sdf
# OR
xr path/to/simulation/*.sdf
```

Below is an example gif of how this interfacing looks as seen on
[xr-tui](https://github.com/samueljackson92/xr-tui) `README.md`:

![xr-tui interfacing gif](https://raw.githubusercontent.com/samueljackson92/xr-tui/main/demo.gif)

## Manipulating data

These datasets can also be easily manipulated the same way as you
would with `numpy` arrays.

```{code-cell} ipython3
ds["Laser_Absorption_Fraction_in_Simulation"] = (
   (ds["Total_Particle_Energy_in_Simulation"] - ds["Total_Particle_Energy_in_Simulation"][0])
   / ds["Absorption_Total_Laser_Energy_Injected"]
) * 100

# We can also manipulate the units and other attributes
ds["Laser_Absorption_Fraction_in_Simulation"].attrs["units"] = "%"
ds["Laser_Absorption_Fraction_in_Simulation"].attrs["long_name"] = "Laser Absorption Fraction"

ds["Laser_Absorption_Fraction_in_Simulation"].epoch.plot()
plt.title("Laser absorption fraction in simulation")
plt.show()
```

You can also call the [`xarray.DataArray.epoch.plot`](project:#sdf_xarray.dataarray_accessor.EpochAccessor.plot) function on several variables with
labels by delaying the call to `plt.show()`.

```{code-cell} ipython3
ds["Total_Particle_Energy_Electron"].epoch.plot(label="Electron")
ds["Total_Particle_Energy_Ion"].epoch.plot(label="Ion")
plt.title("Particle Energy in Simulation per Species")
plt.legend()
plt.show()
```

```{code-cell} ipython3
print(f"Total laser energy injected: {ds["Absorption_Total_Laser_Energy_Injected"][-1].values:.1e} J")
print(f"Total particle energy absorbed: {ds["Total_Particle_Energy_in_Simulation"][-1].values:.1e} J")
print(f"The laser absorption fraction: {ds["Laser_Absorption_Fraction_in_Simulation"][-1].values:.1f} %")
```
