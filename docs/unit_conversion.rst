.. _sec-unit-conversion:

===============
Unit Conversion
===============

``sdf-xarray`` will always attempt to acquire the units for a given dataset from an SDF file and convert them into a ``xarray.Dataset`` attribute called ``units``. This approach is normally fine for most users however we can take this a step further and look to unit conversion using a library called `pint <https://pint.readthedocs.io/en/stable/getting/index.html>`_. This library allows us to specify the units of a given array and convert them to another array which is incredibly handy. We can however take this a step further and utilise the `pint-xarray <https://pint-xarray.readthedocs.io/en/latest/>`_ library which allows us to infer units from an ``xarray.Dataset.attrs`` directly while retaining all the information about ``xarray.Dataset``. 

To install the pint libraries you can simply run the following optional dependency pip command which will install both the ``pint`` and ``pint-xarray`` libraries.

.. code-block:: bash

    pip install "sdf_xarray[pint]"

In the following example we will extract the time-resolved total particle energy of electrons which is measured in Joules and convert it to electron volts. 

.. ipython:: python

    import xarray as xr
    from sdf_xarray import SDFPreprocess
    # If this isn't imported then pint doesn't work
    import pint_xarray

    ds = xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess())

    ds["Total_Particle_Energy_Electron"]
    
    total_particle_energy_ev = ds["Total_Particle_Energy_Electron"].pint.quantify()

    # The units have now disappeared and the regular array has been replaced by a Quantity
    total_particle_energy_ev


Now that this dataset has been converted a ``pint.Quantity`` we can check it's units and dimensionality

.. ipython:: python

    total_particle_energy_ev.pint.units
    total_particle_energy_ev.pint.dimensionality

We can now convert it to electron volts utilising the ``pint.Quantity.to`` function

.. ipython:: python
    
    total_particle_energy_ev = total_particle_energy_ev.pint.to("eV")

Prior to plotting we want to get the units back into the ``xarray.Dataset.attrs`` so that it can be picked up by xarray. While this step isn't necessary it does format the ``units`` attribute as ``"eV"`` instead of ``"electron_volt"``. Other formats are available in the `pint formatting <https://pint.readthedocs.io/en/stable/user/formatting.html>`_ documentation.

.. ipython:: python
    
    total_particle_energy_ev = total_particle_energy_ev.pint.dequantify(format="~P")

To visualise this has worked we can plot the two ``xarray.Dataset``

.. ipython:: python

    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,6))
    ds["Total_Particle_Energy_Electron"].plot(ax=ax1)
    total_particle_energy_ev.plot(ax=ax2)
    @savefig unit_conversion.png width=9in
    fig.suptitle("Comparison of conversion from Joules to electron volts")
    fig.tight_layout()
