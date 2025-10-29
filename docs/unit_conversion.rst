.. _sec-unit-conversion:

===============
Unit Conversion
===============

The ``sdf-xarray`` package automatically extracts the units for each
coordinate/variable/constant from an SDF file and stores them as an :class:`xarray.Dataset`
attribute called ``"units"``. Sometimes we want to convert our data from one format to
another, e.g. converting the grid coordinates from meters to microns, time from seconds 
to femto-seconds or particle energy from Joules to electron-volts.

.. ipython:: python

    from sdf_xarray import open_mfdataset
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "axes.labelsize": 16,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "axes.titlesize": 16
    })


=====================
Rescaling Coordinates
=====================

For simple scaling and unit relabeling of coordinates (e.g., converting meters to microns),
the most straightforward approach is to use the ``rescale_coords()`` method  
via the custom ``xarray.Dataset.epoch`` dataset accessor.  

This method scales the coordinate values by a given multiplier and updates the ``"units"``
attribute in one step.

Rescaling Grid Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~

We can use the ``xarray.Dataset.epoch.rescale_coords()`` method to convert X, Y, and Z
coordinates from meters (m) to microns (µm) by applying a multiplier of ``1e6``.

.. ipython:: python

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    with open_mfdataset("tutorial_dataset_2d/*.sdf") as ds:
        ds_in_microns = ds.epoch.rescale_coords(
            multiplier=1e6, 
            unit_label="µm", 
            coord_names=["X_Grid_mid", "Y_Grid_mid"]
        )
        derived_number_density = ds["Derived_Number_Density_Electron"].isel(time=0).compute()
        derived_number_density_microns = ds_in_microns["Derived_Number_Density_Electron"].isel(time=0).compute()

    derived_number_density.plot(ax=ax1, x="X_Grid_mid", y="Y_Grid_mid")
    ax1.set_title("Original X Coordinate (m)")

    derived_number_density_microns.plot(ax=ax2, x="X_Grid_mid", y="Y_Grid_mid")
    ax2.set_title("Rescaled X Coordinate (µm)")

    @savefig coordinate_conversion.png width=9in
    fig.tight_layout()


Rescaling Time Coordinate
~~~~~~~~~~~~~~~~~~~~~~~~~

We can also use the ``xarray.Dataset.epoch.rescale_coords()`` method to convert the time
coordinate from seconds (s) to femto-seconds (fs) by applying a multiplier of ``1e15``.

.. ipython:: python
    
    with open_mfdataset("tutorial_dataset_2d/*.sdf") as ds:
        ds_time_in_femto = ds.epoch.rescale_coords(
            multiplier=1e15, 
            unit_label="fs", 
            coord_names="time"
        )

        print(f"[Original] units: {ds['time'].attrs['units']}, values: {ds['time'].values}")
        print(f"[Rescaled] units: {ds_time_in_femto['time'].attrs['units']}, values: {ds_time_in_femto['time'].values}")


================================
Unit Conversion with pint-xarray
================================

While this is sufficient for most use cases, we can enhance this functionality
using the `pint <https://pint.readthedocs.io/en/stable/getting/index.html>`_ library.
Pint allows us to specify the units of a given array and convert them
to another, which is incredibly handy. We can take this a step further,
however, and utilize the `pint-xarray
<https://pint-xarray.readthedocs.io/en/latest/>`_ library. This library
allows us to infer units directly from an `xarray.Dataset.attrs` while
retaining all the information about the `xarray.Dataset`. This works
very similarly to taking a NumPy array and multiplying it by a constant or
another array, which returns a new array; however, this library will also
retain the unit logic (specifically the ``"units"`` information).

.. note::
    Unit conversion is not supported on coordinates in ``pint-xarray`` which is due to an
    underlying issue with how ``xarray`` implements indexes.

Installation
~~~~~~~~~~~~

To install the pint libraries you can simply run the following optional
dependency pip command which will install both the ``pint`` and ``pint-xarray``
libraries. You can install these optional dependencies via pip:

.. code:: console

    $ pip install "sdf_xarray[pint]"

.. note::
    Once you install ``pint-xarray`` it is automatically picked up and loaded
    by the code so you should have access to the ``xarray.Dataset.pint`` accessor.

Quantifying Arrays
~~~~~~~~~~~~~~~~~~

When using ``pint-xarray``, the library attempts to infer units from the
``"units"`` attribute on each `xarray.DataArray`. Alternatively, you can
also specify the units yourself by passing a string into the 
``xarray.Dataset.DataArray.pint.quantify()`` function call. Once the type is inferred
the original `xarray.DataArray` will be converted to a `pint.Quantity`
and the ``"units"`` attribute will
be removed.

In the following example we will extract the time-resolved total particle
energy of electrons which is measured in Joules and convert it to electron
volts.

.. ipython:: python

    with open_mfdataset("tutorial_dataset_1d/*.sdf") as ds:
        total_particle_energy = ds["Total_Particle_Energy_Electron"]

    total_particle_energy

    total_particle_energy = ds["Total_Particle_Energy_Electron"].pint.quantify()

    total_particle_energy


Now that this dataset has been converted a `pint.Quantity`, we can check
it's units and dimensionality

.. ipython:: python

    total_particle_energy.pint.units
    total_particle_energy.pint.dimensionality


Converting Units
~~~~~~~~~~~~~~~~

We can now convert it to electron volts utilising the `pint.Quantity.to`
function

.. ipython:: python

    total_particle_energy_ev = total_particle_energy.pint.to("eV")

Unit Propagation
~~~~~~~~~~~~~~~~

Suppose instead of converting to ``"eV"``, we want to convert to ``"W"``
(watts). To do this, we divide the total particle energy by time. However,
since coordinates in `xarray.Dataset` cannot be directly converted to
`pint.Quantity`, we must first extract the coordinate values manually
and create a new Pint quantity for time.

Once both arrays are quantified, Pint will automatically handle the unit
propagation when we perform arithmetic operations like division.

.. note::
    Pint does not automatically simplify ``"J/s"`` to ``"W"``, so we use
    `pint.Quantity.to` to convert the unit string. Since these units are
    the same it will not change the underlying data, only the units. This is
    only a small formatting choice and is not required.

.. ipython:: python

    import pint
    time_values = total_particle_energy.coords["time"].data
    time = pint.Quantity(time_values, "s")
    total_particle_energy_w = total_particle_energy / time
    total_particle_energy_w.pint.units
    total_particle_energy_w = total_particle_energy_w.pint.to("W")
    total_particle_energy_w.pint.units

Dequantifying and Restoring Units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    If this function is not called prior to plotting then the ``units`` will be
    inferred from the `pint.Quantity` array which will return the long
    name of the units. i.e. instead of returning ``"eV"`` it will return
    ``"electron_volt"``.

The ``xarray.Dataset.DataArray.pint.dequantify`` function converts the data from
`pint.Quantity` back to the original `xarray.DataArray` and adds
the ``"units"`` attribute back in. It also has an optional ``format`` parameter
that allows you to specify the formatting type of ``"units"`` attribute. We
have used the ``format="~P"`` option as it shortens the unit to its
"short pretty" format (``"eV"``). For more options, see the `Pint formatting
documentation <https://pint.readthedocs.io/en/stable/user/formatting.html>`_.

.. ipython:: python

    total_particle_energy_ev = total_particle_energy_ev.pint.dequantify(format="~P")
    total_particle_energy_w = total_particle_energy_w.pint.dequantify(format="~P")
    total_particle_energy_ev

To confirm the conversion has worked correctly, we can plot the original and
converted `xarray.Dataset` side by side:

.. ipython:: python
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16,8))
    ds["Total_Particle_Energy_Electron"].plot(ax=ax1)
    total_particle_energy_ev.plot(ax=ax2)
    total_particle_energy_w.plot(ax=ax3)
    ax4.set_visible(False)
    fig.suptitle("Comparison of conversion from Joules to electron volts and watts", fontsize="18")
    @savefig unit_conversion.png width=9in
    fig.tight_layout()
