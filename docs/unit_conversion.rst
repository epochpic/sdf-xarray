.. _sec-unit-conversion:

===============
Unit Conversion
===============

The ``sdf-xarray`` package automatically attempts to extract the units for each dataset from an SDF file and stores them as an :class:`xarray.Dataset` attribute called ``"units"``.

While this is sufficient for most use cases, we can enhance this functionality using the `pint <https://pint.readthedocs.io/en/stable/getting/index.html>`_. This library allows us to specify the units of a given array and convert them to another array which is incredibly handy. We can however take this a step further and utilise the `pint-xarray <https://pint-xarray.readthedocs.io/en/latest/>`_ library which allows us to infer units from an :attr:`xarray.Dataset.attrs` directly while retaining all the information about :class:`xarray.Dataset`. 


Installing pint and pint-xarray
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the pint libraries you can simply run the following optional dependency pip command which will install both the ``pint`` and ``pint-xarray`` libraries. You can install these optional dependencies via pip:

.. code:: console

    $ pip install "sdf_xarray[pint]"

Loading Libraries
~~~~~~~~~~~~~~~~~

First we need to load all the necessary libraries. It's important to import the ``pint_xarray`` library explicitly, even if it appears unused. Without this import, the ``xarray.Dataset.pint`` accessor will not be initialised.

.. ipython:: python

    import xarray as xr
    from sdf_xarray import SDFPreprocess
    import pint_xarray

In the following example we will extract the time-resolved total particle energy of electrons which is measured in Joules and convert it to electron volts.

Quantifying Arrays with Pint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning:: Be aware that unless you're using ``dask`` this will load the data into memory. To avoid that, consider converting to ``dask`` first (e.g. using chunk).

When using ``pint-xarray``, the library attempts to infer units from the ``"units"`` attribute on each :class:`xarray.DataArray`. Alternatively, you can also specify the units yourself by passing a string into the ``xarray.Dataset.pint.quantify()`` function call i.e. ``xarray.Dataset.pint.quantify("J")``. Once the type is inferred the original :class:`xarray.DataArray` will be converted to a :class:`pint.Quantity` and the ``"units"`` attribute will be removed. 

.. note:: Quantification does not alter the underlying data and can be reversed at any time using ``.pint.dequantify()``.

.. ipython:: python

    ds = xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess())

    ds["Total_Particle_Energy_Electron"]
    
    total_particle_energy_ev = ds["Total_Particle_Energy_Electron"].pint.quantify()

    total_particle_energy_ev


Now that this dataset has been converted a :class:`pint.Quantity`, we can check it's units and dimensionality

.. ipython:: python

    total_particle_energy_ev.pint.units
    total_particle_energy_ev.pint.dimensionality


Converting Units (e.g. Joules to eV)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can now convert it to electron volts utilising the :attr:`pint.Quantity.to` function

.. ipython:: python
    
    total_particle_energy_ev = total_particle_energy_ev.pint.to("eV")

Dequantifying and Restoring Units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although this step is optional, it demonstrates how to control the formatting of the restored ``"units"`` attribute. If no format is specified, the unit will be set to ``"electron_volt"`` instead of ``"eV"``. The ``format="~P"`` option shortens the unit string. For more options, see the `Pint formatting documentation <https://pint.readthedocs.io/en/stable/user/formatting.html>`_.

.. ipython:: python
    
    total_particle_energy_ev = total_particle_energy_ev.pint.dequantify(format="~P")
    total_particle_energy_ev

Visualising the Converted Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To confirm the conversion has worked correctly, we can plot the original and converted :class:`xarray.Dataset` side by side:

.. ipython:: python

    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,6))
    ds["Total_Particle_Energy_Electron"].plot(ax=ax1)
    total_particle_energy_ev.plot(ax=ax2)
    @savefig unit_conversion.png width=9in
    fig.suptitle("Comparison of conversion from Joules to electron volts")
    fig.tight_layout()
