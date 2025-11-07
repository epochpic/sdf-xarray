.. _sec-key-functionality:

==================
Key Functionality
==================

.. jupyter-execute::

   import xarray as xr
   import sdf_xarray as sdfxr
   import matplotlib.pyplot as plt
   %matplotlib inline

Loading SDF files
-----------------
There are several ways to load SDF files:

- To load a single file, use `xarray.open_dataset`.
- To load multiple files, use `sdf_xarray.open_mfdataset` or `xarray.open_mfdataset`.
- To access the raw contents of a single SDF file, use `sdf_xarray.sdf_interface.SDFFile`.

.. note::

   When loading SDF files, variables related to ``boundaries``, ``cpu`` and ``output file`` are excluded as they are problematic. If you wish to load these in please use the
   :ref:`loading-raw-files` approach.

.. tip::

    All code examples throughout this documentation are visualised using Jupyter notebooks
    so that you can interactively explore `xarray.Dataset` objects. To do this on your machine
    make sure that you have the necessary dependencies installed: 

    .. code-block:: bash

        pip install "sdf-xarray[jupyter]"

Loading single files
~~~~~~~~~~~~~~~~~~~~

.. jupyter-execute::

   xr.open_dataset("tutorial_dataset_1d/0010.sdf")


.. _loading-raw-files:

Loading raw files
~~~~~~~~~~~~~~~~~

If you wish to load data directly from the ``SDF.C`` library and ignore
the `xarray` interface layer.

.. jupyter-execute::

   raw_ds = sdfxr.SDFFile("tutorial_dataset_1d/0010.sdf")
   raw_ds.variables.keys()

Loading multiple files
~~~~~~~~~~~~~~~~~~~~~~

Multiple files can be loaded using one of two methods. The first of which
is by using the `sdf_xarray.open_mfdataset`.

.. jupyter-execute::

   sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

Alternatively files can be loaded using `xarray.open_mfdataset`
however when loading in all the files we have do some processing of the data
so that we can correctly align it along the time dimension; This is
done via the ``preprocess`` parameter.

.. jupyter-execute::

   xr.open_mfdataset(
      "tutorial_dataset_1d/*.sdf",
      join="outer",
      compat="no_conflicts",
      preprocess=sdfxr.SDFPreprocess()
   )

If your simulation has multiple ``output`` blocks so that not all variables are
output at every time step, then those variables will have ``NaN`` values at the
corresponding time points.

Loading sparse data
~~~~~~~~~~~~~~~~~~~

Alternatively, we can create a separate time dimensions for each ``output``
block using `sdf_xarray.open_mfdataset` with ``separate_times=True``. This is
better for memory consumption, at the cost of perhaps slightly less friendly
comparisons between variables on different time coordinates.

.. jupyter-execute::

    sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", separate_times=True)

Loading particle data
~~~~~~~~~~~~~~~~~~~~~

.. warning::
   It is **not recommended** to use `xarray.open_mfdataset` or
   `sdf_xarray.open_mfdataset` to load particle data from multiple
   SDF outputs. The number of particles often varies between outputs,
   which can lead to inconsistent array shapes that these functions
   cannot handle. Instead, consider loading each file individually and
   then concatenating them manually.

.. note::
   When loading multiple probes from a single SDF file, you **must** use the
   ``probe_names`` parameter to assign a unique name to each. For example,
   use ``probe_names=["Front_Electron_Probe", "Back_Electron_Probe"]``.
   Failing to do so will result in dimension name conflicts.

By default, particle data isn't kept as it takes up a lot of space.
Pass ``keep_particles=True`` as a keyword argument to
`xarray.open_dataset` (for single files) or `xarray.open_mfdataset` (for
multiple files).

.. jupyter-execute::

   xr.open_dataset("tutorial_dataset_1d/0010.sdf", keep_particles=True)

Data interaction examples
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

.. jupyter-execute::

   ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

   ds["Electric_Field_Ex"]

On top of accessing variables you can plot these `xarray.Dataset`
using the built-in `xarray.DataArray.plot` function (see
https://docs.xarray.dev/en/stable/user-guide/plotting.html) which is
a simple call to ``matplotlib``. This also means that you can access
all the methods from ``matplotlib`` to manipulate your plot.

.. jupyter-execute::

   # This is discretized in both space and time
   ds["Electric_Field_Ex"].plot()
   plt.title("Electric field along the x-axis")
   plt.show()

After having loaded in a series of datasets we can select a
simulation file by calling the `xarray.Dataset.isel` function where we pass in
the parameter of ``time=0`` where ``0`` can be a number between ``0``
and the total number of simulation files.

We can also use the `xarray.Dataset.sel` function if we know the exact
simulation time we want to select. There must be a corresponding
dataset with this time for it work correctly.

.. jupyter-execute::

   # This is the same as the number of SDF files in the folder
   print(f"There are a total of {ds["time"].size} time steps")

   # The time at the 20th simulation step
   sim_time = ds['time'].isel(time=20).values
   print(f"The time at the 20th simulation step is {sim_time:.2e} s")

   # We can plot the variable at a given time index
   ds["Electric_Field_Ex"].isel(time=20).plot()
   # Or we can plot the variable at a specific value of the time
   # ds["Electric_Field_Ex"].sel(time=sim_time).plot()
   plt.show()

Manipulating data
-----------------

These datasets can also be easily manipulated the same way as you
would with ``numpy`` arrays.

.. jupyter-execute::

   ds["Laser_Absorption_Fraction_in_Simulation"] = (
      ds["Total_Particle_Energy_in_Simulation"]
      / ds["Absorption_Total_Laser_Energy_Injected"]
   ) * 100

   # We can also manipulate the units and other attributes
   ds["Laser_Absorption_Fraction_in_Simulation"].attrs["units"] = "%"
   ds["Laser_Absorption_Fraction_in_Simulation"].attrs["long_name"] = "Laser Absorption Fraction"

   ds["Laser_Absorption_Fraction_in_Simulation"].plot()
   plt.title("Laser absorption fraction in simulation")
   plt.show()

You can also call the ``plot()`` function on several variables with
labels by delaying the call to ``plt.show()``.

.. jupyter-execute::

   ds["Total_Particle_Energy_Electron"].plot(label="Electron")
   ds["Total_Particle_Energy_Photon"].plot(label="Photon")
   ds["Total_Particle_Energy_Ion"].plot(label="Ion")
   ds["Total_Particle_Energy_Positron"].plot(label="Positron")
   plt.title("Particle Energy in Simulation per Species")
   plt.legend()
   plt.show()


.. jupyter-execute::

   print(f"Total laser energy injected: {ds["Absorption_Total_Laser_Energy_Injected"].max().values:.1e} J")
   print(f"Total particle energy absorbed: {ds["Total_Particle_Energy_in_Simulation"].max().values:.1e} J")
   print(f"The laser absorption fraction: {ds["Laser_Absorption_Fraction_in_Simulation"].max().values:.1f} %")
