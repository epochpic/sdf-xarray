---
file_format: mystnb
kernelspec:
  name: python3
---

# Unit Conversion

The <project:#sdf_xarray> package automatically extracts the units for each
coordinate/variable/constant from an SDF file and stores them as an <inv:#xarray.Dataset>
attribute called `"units"`. Sometimes we want to convert our data from one format to
another, e.g. converting the grid coordinates from meters to microns, time from seconds
to femto-seconds or particle energy from Joules to electron-volts.

```{code-cell} ipython3
import sdf_xarray as sdfxr
import matplotlib.pyplot as plt

plt.rcParams.update({
    "axes.labelsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "axes.titlesize": 16,
    "figure.titlesize": 18,
})
```

## Rescaling coordinates

For simple scaling and unit relabelling of coordinates (e.g., converting meters to microns),
the most straightforward approach is to use the [`xarray.Dataset.epoch.rescale_coords`](project:#sdf_xarray.dataset_accessor.EpochAccessor.rescale_coords) dataset accessor.
This function scales the coordinate values by a given multiplier and updates the
`"units"` attribute in one step. If the multiplier is not specified then the conversion parameter is inferred from the units and converted automatically using `pint` (see [](#unit-conversion-with-pint-xarray) for details).

### Rescaling grid coordinates

We can use the [`xarray.Dataset.epoch.rescale_coords`](project:#sdf_xarray.dataset_accessor.EpochAccessor.rescale_coords) method to convert X, Y, and Z coordinates from meters
(`m`) to microns (`µm`) by applying a multiplier of `1e6`.

```{code-cell} ipython3
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

ds = sdfxr.open_mfdataset("tutorial_dataset_2d/*.sdf")
ds_in_microns = ds.epoch.rescale_coords("µm", ["X_Grid_mid", "Y_Grid_mid"], 1e6)

ds["Derived_Number_Density_Electron"].isel(time=0).epoch.plot(ax=ax1)
ax1.set_title("Original X Coordinate (m)")

ds_in_microns["Derived_Number_Density_Electron"].isel(time=0).epoch.plot(ax=ax2)
ax2.set_title("Rescaled X Coordinate (µm)")

fig.tight_layout()
```

### Rescaling time coordinate

We can also use the [`xarray.Dataset.epoch.rescale_coords`](project:#sdf_xarray.dataset_accessor.EpochAccessor.rescale_coords) method to convert the time coordinate from
seconds (`s`) to femto-seconds (`fs`).

```{code-cell} ipython3
ds = sdfxr.open_mfdataset("tutorial_dataset_2d/*.sdf")
ds["time"]
```

```{code-cell} ipython3
ds = ds.epoch.rescale_coords("fs", "time")
ds["time"]
```

## Unit conversion with pint-xarray

While this is sufficient for most use cases, we can enhance this functionality
using the [pint](https://pint.readthedocs.io/en/stable) library.
Pint allows us to specify the units of a given array and convert them
to another, which is incredibly handy. We can take this a step further,
however, and utilize the [pint-xarray](https://pint-xarray.readthedocs.io/en/stable)
library. This library allows us to infer units directly from an
<inv:#xarray.Dataset.attrs> while retaining all the information about the
<inv:#xarray.Dataset>. This works very similarly to taking a NumPy array and
multiplying it by a constant or another array, which returns a new array;
however, this library will also retain the unit logic (specifically the
`"units"` information).

```{note}
Unit conversion is not supported on coordinates in `pint_xarray` which is due to an
underlying issue with how <inv:#xarray> implements indexes.
```

### Installation

To install the pint libraries you can simply run the following optional
dependency pip command which will install both the `pint` and `pint_xarray`
libraries. Once installed the
[`xarray.Dataset.pint`](https://pint-xarray.readthedocs.io/en/stable/api.html#dataset)
accessor should become accessible. You can install these optional dependencies via pip:

```bash
pip install "sdf_xarray[pint]"
```

### Quantifying DataArrays

When using `pint_xarray`, the library attempts to infer units from the
`"units"` attribute on each <inv:#xarray.DataArray>. In the following example we will
extract the time-resolved total particle energy of electrons which is measured in
Joules and convert it to electron volts.

```{code-cell} ipython3
ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")
ds["Total_Particle_Energy_Electron"]
```

Once you call <inv:#xarray.DataArray.pint.quantify> the type is inferred the original
<inv:#xarray.DataArray> `"units"` attribute which is then removed and the data is
converted to a <inv:#pint.Quantity>.

```{note}
You can also specify the units yourself by passing it as a string
(e.g. `"J"`) into the <inv:#xarray.DataArray.pint.quantify> function call.
```

```{code-cell} ipython3
total_particle_energy = ds["Total_Particle_Energy_Electron"].pint.quantify()
total_particle_energy
```

Now that this dataset has been converted a <inv:#pint.Quantity>, we can check
it's units and dimensionality

```{code-cell} ipython3
print(total_particle_energy.pint.units)
print(total_particle_energy.pint.dimensionality)
```

### Converting units

We can now convert it to electron volts utilising the <inv:#xarray.DataArray.pint.to>
function

```{code-cell} ipython3
total_particle_energy_ev = total_particle_energy.pint.to("eV")
total_particle_energy_ev
```

### Unit propagation

Suppose instead of converting to `"eV"`, we want to convert to `"W"`
(watts). To do this, we divide the total particle energy by time. However,
since coordinates in <inv:#xarray.Dataset> cannot be directly converted to
<inv:#pint.Quantity>, we must first extract the coordinate values manually
and create a new Pint quantity for time.

Once both arrays are quantified, Pint will automatically handle the unit
propagation when we perform arithmetic operations like division.

```{note}
Pint does not automatically simplify `"J/s"` to `"W"`, so we use
<inv:#xarray.DataArray.pint.to> to convert the unit string. Since
these units are the same it will not change the underlying data, only the
units. This is only a small formatting choice and is not required.
```

```{code-cell} ipython3
import pint

time_values = total_particle_energy.coords["time"].data
time = pint.Quantity(time_values, "s")
total_particle_energy_w = total_particle_energy / time # units: joule / second
total_particle_energy_w = total_particle_energy_w.pint.to("W") # units: watt
```

### Dequantifying and restoring units

```{note}
If this function is not called prior to plotting then the `units` will be
inferred from the <inv:#pint.Quantity> array which will return the long
name of the units. i.e. instead of returning `"eV"` it will return
`"electron_volt"`.
```

The <inv:#xarray.DataArray.pint.dequantify> function converts the data from
<inv:#pint.Quantity> back to the original <inv:#xarray.DataArray> and adds
the `"units"` attribute back in. It also has an optional `format` parameter
that allows you to specify the formatting type of `"units"` attribute. We
have used the `format="~P"` option as it shortens the unit to its
"short pretty" format (`"eV"`). For more options, see the
[Pint formatting documentation](https://pint.readthedocs.io/en/stable/user/formatting.html).

```{code-cell} ipython3
total_particle_energy_ev = total_particle_energy_ev.pint.dequantify(format="~P")
total_particle_energy_w = total_particle_energy_w.pint.dequantify(format="~P")
total_particle_energy_ev
```

To confirm the conversion has worked correctly, we can plot the original and
converted <inv:#xarray.Dataset> side by side:

```{code-cell} ipython3
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16,8))
ds["Total_Particle_Energy_Electron"].epoch.plot(ax=ax1)
total_particle_energy_ev.epoch.plot(ax=ax2)
total_particle_energy_w.epoch.plot(ax=ax3)
ax4.set_visible(False)
fig.suptitle("Comparison of conversion from Joules to electron volts and watts")
fig.tight_layout()
```
