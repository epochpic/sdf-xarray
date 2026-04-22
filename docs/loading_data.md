---
file_format: mystnb
kernelspec:
  name: python3
---

# Loading SDF Files

There are two main ways to load [EPOCH SDF files](https://epochpic.github.io/documentation/visualising_output.html)
into <inv:#xarray> objects; using the dedicated <project:#sdf_xarray> functions or
using the standard <inv:#xarray> interface with our custom engine. 

The <project:#sdf_xarray> functions are wrappers designed specifically for SDF data, providing the most
straightforward experience:

- **Single files**: Use <project:#sdf_xarray.open_dataset> or <project:#sdf_xarray.open_datatree>
- **Multiple files**: Use <project:#sdf_xarray.open_mfdataset> or <project:#sdf_xarray.open_mfdatatree>
- **Raw files**: use <project:#sdf_xarray.sdf_interface.SDFFile>

If you prefer using the native <inv:#xarray> functions, you can use the <inv:#xarray.open_dataset>,
<inv:#xarray.open_datatree> and <inv:#xarray.open_mfdataset>. Strangely there is no function in
<inv:#xarray> for `xarray.open_mfdatatree`.

These functions should all work out of the box as long as <project:#sdf_xarray> is installed on your
system. If you are having issues reading files, you might need to pass the parameter
`engine=sdf_engine` when calling any of the above xarray functions.

```{important}
When loading SDF files, variables related to `boundaries`, `cpu` and `output file`
are excluded as they are problematic. If you wish to load these variables in see
<project:#loading-raw-files>.
```

````{note}
All code examples shown here are visualised using [Jupyter notebooks](https://jupyter.org/)
so that you can interactively explore the datasets. To do this on your machine
make sure that you have the necessary dependencies installed:

```bash
uv pip install "sdf-xarray[jupyter]"
```

Additionally, if you wish to follow along using the same datasets featured in this documentation, 
you can download them from Zenodo ([10.5281/zenodo.17618509](https://doi.org/10.5281/zenodo.17618509))
using <project:#sdf_xarray.download.fetch_dataset>.
````

## Loading single files

```{code-cell} ipython3
import sdf_xarray as sdfxr

sdfxr.open_dataset("tutorial_dataset_1d/0010.sdf")
```

You can also load the data in as a <inv:#xarray.DataTree>, which organises the data
hierarchically into `groups` (for example grouping related quantities such as the individual
components of the electric and magnetic fields) while keeping each item as a <inv:#xarray.Dataset>.

```{code-cell} ipython3
import sdf_xarray as sdfxr

sdfxr.open_datatree("tutorial_dataset_1d/0010.sdf")
```

(loading-raw-files)=

## Loading raw files

If you wish to load data directly from the `SDF.C` library and ignore
the <inv:#xarray> interface layer.

```{code-cell} ipython3
import sdf_xarray as sdfxr

raw_ds = sdfxr.SDFFile("tutorial_dataset_1d/0010.sdf")
raw_ds.variables.keys()
```

## Loading multiple files

Multiple files can be loaded using one of two methods. The first of which
is by using the <project:#sdf_xarray.open_mfdataset>.

```{tip}
If your simulation includes multiple `output` blocks that specify different variables
for output at various time steps, variables not present at a specific step will default
to a nan value. To remove these nan values we suggest using the <inv:#xarray.DataArray.dropna>
function or following our implmentation in [](#loading-sparse-data).
```

```{code-cell} ipython3
import sdf_xarray as sdfxr

sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")
```

Alternatively, files can be loaded using <inv:#xarray.open_mfdataset>. However, when loading in
all the files we have do some processing of the data so that we can correctly align it along
the time dimension; This is done via the `preprocess` parameter utilising the
<project:#sdf_xarray.SDFPreprocess> function.

```{code-cell} ipython3
import xarray as xr

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
import sdf_xarray as sdfxr

sdfxr.open_mfdatatree("tutorial_dataset_1d/*.sdf")
```

## Loading sparse data

When dealing with sparse data (where different variables are saved at different,
non-overlapping time steps) you can optimize memory usage by loading the data with
<project:#sdf_xarray.open_mfdataset> using the parameter `separate_times=True`. This
approach creates a distinct time dimension for each output block, avoiding the
need for a single, large time dimension that would be filled with nan values. This
significantly reduces memory consumption, though it requires more deliberate handling
if you need to compare variables that exist on these different time coordinates.

```{code-cell} ipython3
import sdf_xarray as sdfxr

sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", separate_times=True)
```

## Loading particle data

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
import sdf_xarray as sdfxr

sdfxr.open_dataset("tutorial_dataset_1d/0010.sdf", keep_particles=True)
```

## Loading specific variables

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
import sdf_xarray as sdfxr

sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", data_vars=["Electric_Field_Ex"])
```

(loading-input-deck)=

## Loading the input.deck

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
import sdf_xarray as sdfxr

ds = sdfxr.open_dataset("tutorial_dataset_1d/0010.sdf")
# The results are accessible by calling
deck = ds.attrs["deck"]

# Some prettification to make it looks nice in jupyter notebooks
json_str = json.dumps(deck, indent=4)
Code(json_str, language='json')
```