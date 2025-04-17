.. _sec-unit-conversion:

===============
Unit Conversion
===============

The ``sdf-xarray`` package automatically attempts to extract the units for each
dataset from an SDF file and stores them as an :class:`xarray.Dataset`
attribute called ``"units"``.

While this is sufficient for most use cases, we can enhance this functionality
using the `pint <https://pint.readthedocs.io/en/stable/getting/index.html>`_.
This library allows us to specify the units of a given array and convert them
to another array which is incredibly handy. We can however take this a step
further and utilise the `pint-xarray
<https://pint-xarray.readthedocs.io/en/latest/>`_ library which allows us to
infer units from an :attr:`xarray.Dataset.attrs` directly while retaining all
the information about :class:`xarray.Dataset`.


Installing pint and pint-xarray
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the pint libraries you can simply run the following optional
dependency pip command which will install both the ``pint`` and ``pint-xarray``
libraries. You can install these optional dependencies via pip:

.. code:: console

    $ pip install "sdf_xarray[pint]"

Loading Libraries
~~~~~~~~~~~~~~~~~

First we need to load all the necessary libraries. It's important to import the
``pint_xarray`` library explicitly, even if it appears unused. Without this
import, the ``xarray.Dataset.pint`` accessor will not be initialised.

.. ipython:: python

    import xarray as xr
    from sdf_xarray import SDFPreprocess
    import pint_xarray

In the following example we will extract the time-resolved total particle
energy of electrons which is measured in Joules and convert it to electron
volts.

Quantifying Arrays with Pint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
    Be aware that unless you're using ``dask`` this will load the data into
    memory. To avoid that, consider converting to ``dask`` first
    (e.g. using chunk).

When using ``pint-xarray``, the library attempts to infer units from the
``"units"`` attribute on each :class:`xarray.DataArray`. Alternatively, you can
also specify the units yourself by passing a string into the ``xarray.Dataset
.pint.quantify()`` function call i.e. ``xarray.Dataset.pint.quantify("J")``.
Once the type is inferred the original :class:`xarray.DataArray` will be
converted to a :class:`pint.Quantity` and the ``"units"`` attribute will
be removed.

.. note::
    Quantification does not alter the underlying data and can be reversed at
    any time using ``.pint.dequantify()``.

.. warning::
    Unit conversion is not supported on coordinates, this is due to an
    underlying issue with how ``xarray`` implements indexes

.. ipython:: python

    with xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess()) as ds:
        total_particle_energy = ds["Total_Particle_Energy_Electron"]

    total_particle_energy

    total_particle_energy = ds["Total_Particle_Energy_Electron"].pint.quantify()

    total_particle_energy


Now that this dataset has been converted a :class:`pint.Quantity`, we can check
it's units and dimensionality

.. ipython:: python

    total_particle_energy.pint.units
    total_particle_energy.pint.dimensionality


Converting Units (e.g. Joules to eV)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can now convert it to electron volts utilising the :attr:`pint.Quantity.to`
function

.. ipython:: python

    total_particle_energy_ev = total_particle_energy.pint.to("eV")

Unit Propagation
~~~~~~~~~~~~~~~~

Suppose instead of converting to ``"eV"``, we want to convert to ``"W"``
(watts). To do this, we divide the total particle energy by time. However,
since coordinates in :class:`xarray.Dataset` cannot be directly converted to
:class:`pint.Quantity`, we must first extract the coordinate values manually
and create a new Pint quantity for time.

Once both arrays are quantified, Pint will automatically handle the unit
propagation when we perform arithmetic operations like division.

.. note::
    Pint does not automatically simplify ``"J/s"`` to ``"W"``, so we use
    :attr:`pint.Quantity.to` to convert the unit string. Since these units are
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
    inferred from the :class:`pint.Quantity` array which will return the long
    name of the units. i.e. instead of returning ``"eV"`` it will return
    ``"electron_volt"``.

The ``xarray.Dataset.pint.dequantify`` function converts the data from
:class:`pint.Quantity` back to the original :class:`xarray.DataArray` and adds
the ``"units"`` attribute back in. It also has an optional ``format`` parameter
that allows you to specify the formatting type of ``"units"`` attribute. We
have used the ``format="~P"`` option as it shortens the unit to its
"short pretty" format (``"eV"``). For more options, see the `Pint formatting
documentation <https://pint.readthedocs.io/en/stable/user/formatting.html>`_.

.. ipython:: python

    total_particle_energy_ev = total_particle_energy_ev.pint.dequantify(format="~P")
    total_particle_energy_w = total_particle_energy_w.pint.dequantify(format="~P")
    total_particle_energy_ev

Visualising the Converted Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To confirm the conversion has worked correctly, we can plot the original and
converted :class:`xarray.Dataset` side by side:

.. ipython:: python

    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "axes.labelsize": 16,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14
    })
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16,8))
    ds["Total_Particle_Energy_Electron"].plot(ax=ax1)
    total_particle_energy_ev.plot(ax=ax2)
    total_particle_energy_w.plot(ax=ax3)
    ax4.set_visible(False)
    fig.suptitle("Comparison of conversion from Joules to electron volts and watts", fontsize="18")
    @savefig unit_conversion.png width=9in
    fig.tight_layout()
