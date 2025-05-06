.. _sec-key-functionality:

==================
Key Functionality
==================

.. ipython:: python

   import matplotlib.pyplot as plt
   from IPython.display import display, HTML
   import xarray as xr
   from sdf_xarray import SDFFile, SDFPreprocess

Loading SDF Files
-----------------
There are several ways to load SDF files:

- To load a single file, use :func:`xarray.open_dataset`.
- To load multiple files, use :func:`xarray.open_mfdataset` or :func:`sdf_xarray.open_mfdataset`.
- To access the raw contents of a single SDF file, use :func:`sdf_xarray.sdf_interface.SDFFile`.

.. note::
   When loading ``*.sdf`` files, variables related to ``boundaries``, ``cpu`` and ``output file`` are excluded as they are problematic.

Loading a Single SDF File
~~~~~~~~~~~~~~~~~~~~~~~~~

.. ipython:: python

   xr.open_dataset("tutorial_dataset_1d/0010.sdf")

Loading a Single Raw SDF File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. ipython:: python

   with SDFFile("tutorial_dataset_1d/0010.sdf") as sdf_file:
      print(sdf_file.variables)

Loading all SDF Files for a Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When loading in all the files we have do some processing of the data
so that we can correctly align it along the time dimension; This is
done via the ``preprocess`` parameter.

.. ipython:: python

   xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess())

Reading particle data
~~~~~~~~~~~~~~~~~~~~~

By default, particle data isn't kept as it takes up a lot of space.
Pass ``keep_particles=True`` as a keyword argument to
:func:`xarray.open_dataset` (for single files) or :func:`xarray.open_mfdataset` (for
multiple files)

.. ipython:: python

   xr.open_dataset("tutorial_dataset_1d/0010.sdf", keep_particles=True)

Data Interaction examples
-------------------------

When loading in either a single dataset or a group of datasets you
can access the following methods to explore the dataset:

-  ``ds.variables`` to list variables. (e.g. Electric Field, Magnetic
   Field, Particle Count)
-  ``ds.coords`` for accessing coordinates/dimensions. (e.g. x-axis,
   y-axis, time)
-  ``ds.attrs`` for metadata attached to the dataset. (e.g. filename,
   step, time)

It is important to note here that ``xarray`` lazily loads the data
meaning that it only explicitly loads the results your currently
looking at when you call ``.values``

.. ipython:: python

   ds = xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess())

   ds["Electric_Field_Ex"]

On top of accessing variables you can plot these :class:`xarray.Dataset`
using the built-in :meth:`xarray.DataArray.plot()` function (see
https://docs.xarray.dev/en/stable/user-guide/plotting.html) which is
a simple call to ``matplotlib``. This also means that you can access
all the methods from ``matplotlib`` to manipulate your plot.

.. ipython:: python
   :okwarning:

   # This is discretized in both space and time
   ds["Electric_Field_Ex"].plot()
   @savefig electric_field_ex.png width=6in
   plt.title("Electric Field along the x-axis")

After having loaded in a series of datasets we can select a
simulation file by calling the :meth:`xarray.Dataset.isel()` function where we pass in
the parameter of ``time=0`` where ``0`` can be a number between ``0``
and the total number of simulation files.

We can also use the :meth:`xarray.Dataset.sel()` function if we know the exact
simulation time we want to select. There must be a corresponding
dataset with this time for it work correctly.

.. ipython:: python

   print(f"There are a total of {ds["time"].size} time steps. (This is the same as the number of SDF files in the folder)")
   print("The time steps are: ")
   print(ds["time"].values)

   # The time at the 20th simulation step
   sim_time = ds['time'].isel(time=20).values
   print(f"The time at the 20th simulation step is {sim_time:.2e} s")

   # We can plot the time using either the isel or sel method passing in either the index or the value of the time
   ds["Electric_Field_Ex"].isel(time=20).plot()
   # ds["Electric_Field_Ex"].sel(time=sim_time).plot()
   @savefig electric_field_ex_time.png width=6in
   plt.title(f"Electric Field along the x-axis at {sim_time:.2e} s")

Manipulating Data
-----------------

These datasets can also be easily manipulated the same way as you
would with ``numpy`` arrays

.. ipython:: python

   ds["Laser_Absorption_Fraction_in_Simulation"] = (ds["Total_Particle_Energy_in_Simulation"] / ds["Absorption_Total_Laser_Energy_Injected"]) * 100
   # We can also manipulate the units and other attributes
   ds["Laser_Absorption_Fraction_in_Simulation"].attrs["units"] = "%"

   ds["Laser_Absorption_Fraction_in_Simulation"].plot()
   @savefig absorption_fraction.png width=6in
   plt.title("Laser Absorption Fraction in Simulation")

You can also call the ``plot()`` function on several variables with
labels by delaying the call to ``plt.show()``

.. ipython:: python

   print(f"The total laser energy injected into the simulation is {ds["Absorption_Total_Laser_Energy_Injected"].max().values:.1e} J")
   print(f"The total particle energy absorbed by the simulation is {ds["Total_Particle_Energy_in_Simulation"].max().values:.1e} J")
   print(f"The laser absorption fraction in the simulation is {ds["Laser_Absorption_Fraction_in_Simulation"].max().values:.1f} %")
   ds["Total_Particle_Energy_Electron"].plot(label="Electron")
   ds["Total_Particle_Energy_Photon"].plot(label="Photon")
   ds["Total_Particle_Energy_Ion"].plot(label="Ion")
   ds["Total_Particle_Energy_Positron"].plot(label="Positron")
   plt.legend()
   @savefig absorption_fraction_species.png width=6in
   plt.title("Particle Energy in Simulation per Species")
