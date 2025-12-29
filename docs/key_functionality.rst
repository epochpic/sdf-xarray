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

- To load a single file, use `xarray.open_dataset`, `sdf_xarray.open_datatree` or `xarray.open_datatree`
- To load multiple files, use `sdf_xarray.open_mfdataset`, `xarray.open_mfdataset` or `sdf_xarray.open_mfdatatree`.
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

Alternatively, you can load the data in as a `xarray.DataTree`, which organises the data
hierarchically into ``groups`` (for example grouping related quantities such as the individual
components of the electric and magnetic fields) while keeping each item as a `xarray.Dataset`.

.. jupyter-execute::

   sdfxr.open_datatree("tutorial_dataset_1d/0010.sdf")

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

.. tip::

   If your simulation includes multiple ``output`` blocks that specify different variables
   for output at various time steps, variables not present at a specific step will default
   to a nan value. To clean your dataset by removing these nan values we suggest using the
   `xarray.DataArray.dropna` function or :ref:`loading-sparse-data`.

.. jupyter-execute::

   sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

Alternatively, you can load the data in as a `xarray.DataTree`, which organises the data
hierarchically into ``groups`` (for example grouping related quantities such as the individual
components of the electric and magnetic fields) while keeping each item as a `xarray.Dataset`.

.. jupyter-execute::

   sdfxr.open_mfdatatree("tutorial_dataset_1d/*.sdf")

Alternatively files can be loaded using `xarray.open_mfdataset` however when loading in
all the files we have do some processing of the data so that we can correctly align it along
the time dimension; This is done via the ``preprocess`` parameter utilising the
`sdf_xarray.SDFPreprocess` function.

.. jupyter-execute::

   xr.open_mfdataset(
      "tutorial_dataset_1d/*.sdf",
      join="outer",
      compat="no_conflicts",
      preprocess=sdfxr.SDFPreprocess()
   )

.. _loading-sparse-data:

Loading sparse data
~~~~~~~~~~~~~~~~~~~

When dealing with sparse data (where different variables are saved at different,
non-overlapping time steps) you can optimize memory usage by loading the data with
`sdf_xarray.open_mfdataset` using the parameter ``separate_times=True``. This
approach creates a distinct time dimension for each output block, avoiding the
need for a single, large time dimension that would be filled with nan values. This
significantly reduces memory consumption, though it requires more deliberate handling
if you need to compare variables that exist on these different time coordinates.

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

Loading specific variables
~~~~~~~~~~~~~~~~~~~~~~~~~~

When loading datasets containing several (``>10``) coordinates/dimensions
using `sdf_xarray.open_mfdataset`, ``xarray`` may struggle to locate
the necessary RAM to concatenate all of the data (as seen in
`Issue #57 <https://github.com/epochpic/sdf-xarray/issues/57>`_).
In this instance, you can optimize memory usage by loading only the data
you need using the keyword argument ``data_vars`` and passing one or more
variables. This creates a dataset consisting only of the given variable(s)
and the relevant coordinates/dimensions, significantly reducing memory
consumption.

.. jupyter-execute::

   sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", data_vars=["Electric_Field_Ex"])

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

When loading a multi-file dataset using `sdf_xarray.open_mfdataset`, a
time dimension is automatically added to the resulting `xarray.Dataset`.
This dimension represents all the recorded simulation steps and allows
for easy indexing. To quickly determine the number of time steps available,
you can check the size of the time dimension.

.. jupyter-execute::

   # This corresponds to the number of individual SDF files loaded
   print(f"There are a total of {ds['time'].size} time steps")

   # You can look up the actual simulation time for any given index
   sim_time = ds['time'].values[20]
   print(f"The time at the 20th simulation step is {sim_time:.2e} s")

You can select and extract a single simulation snapshot using the integer
index of the time step with the `xarray.Dataset.isel` function. This can be
done by passsing the index to the ``time`` parameter (e.g., ``time=0`` for
the first snapshot).

.. jupyter-execute::

   # We can plot the variable at a given time index
   ds["Electric_Field_Ex"].isel(time=20)

We can also use the `xarray.Dataset.sel` function if you wish to pass a
value intead of an index.

.. tip::

   If you know roughly what time you wish to select but not the exact value
   you can use the parameter ``method="nearest"``.

.. jupyter-execute::

   ds["Electric_Field_Ex"].sel(time=sim_time)

Manipulating data
-----------------

These datasets can also be easily manipulated the same way as you
would with ``numpy`` arrays.

.. jupyter-execute::

   ds["Laser_Absorption_Fraction_in_Simulation"] = (
      (ds["Total_Particle_Energy_in_Simulation"] - ds["Total_Particle_Energy_in_Simulation"][0])
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
   ds["Total_Particle_Energy_Ion"].plot(label="Ion")
   plt.title("Particle Energy in Simulation per Species")
   plt.legend()
   plt.show()


.. jupyter-execute::

   print(f"Total laser energy injected: {ds["Absorption_Total_Laser_Energy_Injected"][-1].values:.1e} J")
   print(f"Total particle energy absorbed: {ds["Total_Particle_Energy_in_Simulation"][-1].values:.1e} J")
   print(f"The laser absorption fraction: {ds["Laser_Absorption_Fraction_in_Simulation"][-1].values:.1f} %")
