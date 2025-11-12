.. _sec-animation:

.. |animate_accessor| replace:: `xarray.DataArray.epoch.animate
   <sdf_xarray.plotting.animate>`

==========
Animations
==========

|animate_accessor| creates a `matplotlib.animation.FuncAnimation`; it is
designed to mimic `xarray.DataArray.plot`.

.. jupyter-execute::

   import sdf_xarray as sdfxr
   import xarray as xr
   import matplotlib.pyplot as plt
   from matplotlib.animation import FuncAnimation
   from IPython.display import HTML

Basic usage
-----------

The type of plot that is animated is determined by the dimensionality of the `xarray.DataArray` object.

.. note::
   ``time`` is considered a dimension in the same way as spatial co-ordinates, so 1D time
   resolved data has 2 dimensions.

.. csv-table::
  :header: "Dimensions", "Plotting function", "Notes"
  :widths: auto
  :align: center

  "2",  "`xarray.plot.line`",       ""
  "3",  "`xarray.plot.pcolormesh`", ""
  ">3", "`xarray.plot.hist`",       "Not fully implemented"


1D simulation
~~~~~~~~~~~~~

We can animate a variable of a 1D simulation in the following way.
It is important to note that since the dataset is time resolved, it has
2 dimensions.

.. warning::
   ``anim.show()`` will only show the animation in a Jupyter notebook.

.. jupyter-execute::

   # Open the SDF files
   ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")
   
   # Get the DataArray variable out of the Dataset
   da = ds["Derived_Number_Density_Electron"]

   # Create the FuncAnimation object
   anim = da.epoch.animate()
   
   # Display animation as jshtml
   anim.show()

.. tip::
   The animations can be saved with

   .. code-block:: bash

      anim.save("path/to/save/animation.gif")
   
   where ``.gif`` can be replaced with any supported file format.

   It can also be shown in a regular python interface with

   .. code-block:: bash

      fig, ax = plt.subplots()
      anim = da.epoch.animate(ax=ax)
      plt.show()

2D simulation
~~~~~~~~~~~~~

Plotting a 2D simulation can be done in exactly the same way.

.. jupyter-execute::

   ds = sdfxr.open_mfdataset("tutorial_dataset_2d/*.sdf")
   da = ds["Derived_Number_Density_Electron"]
   anim = da.epoch.animate()
   anim.show()

We can also take a lineout of a 2D simulation to create 2D data and
plot it as a `xarray.plot.line`.

.. jupyter-execute::
   
   da = ds["Derived_Number_Density_Electron"]
   da_lineout = da.sel(Y_Grid_mid = 1e-6, method = "nearest")
   anim = da_lineout.epoch.animate(title = "Y = 1e-6 [m]")
   anim.show()

3D simulation
~~~~~~~~~~~~~

Opening a 3D simulation as a multi-file dataset and plotting it will
automatically return a `xarray.plot.hist`, this however might not be
desirable. We can plot a 3D simulation along a certain plane in the
same way a 2D simulation can be plotted along a line.

.. jupyter-execute::
   
   ds = sdfxr.open_mfdataset("tutorial_dataset_3d/*.sdf")

   da = ds["Derived_Number_Density"]
   da_lineout = da.sel(Y_Grid_mid = 0, method="nearest")
   anim = da_lineout.epoch.animate(title = "Y = 0 [m]", fps = 2)
   anim.show()

A single SDF file can be animated by changing the time coordinate of
the animation.

.. jupyter-execute::
   
   ds = xr.open_dataset("tutorial_dataset_3d/0005.sdf")
   da = ds["Derived_Number_Density"]
   anim = da.epoch.animate(t = "X_Grid_mid")
   anim.show()

Moving window
-------------

EPOCH allows for simulations that have a moving simulation window
(changing x-axis over time). |animate_accessor| will
automatically detect when a simulation has a moving window by searching 
for NaNs in the `xarray.DataArray`; and change the x-axis limits
accordingly.

.. warning::
   `sdf_xarray.open_mfdataset` does not currently function with moving window data.
   You must use `xarray.open_mfdataset` and specify arguments in the following way.

.. jupyter-execute::

   ds = xr.open_mfdataset(
      "tutorial_dataset_2d_moving_window/*.sdf",
      preprocess = sdfxr.SDFPreprocess(),
      combine = "nested",
      join = "outer",
      compat="no_conflicts",
      concat_dim="time",
      )

   da = ds["Derived_Number_Density_Beam_Electrons"]
   anim = da.epoch.animate(fps = 5)
   anim.show()

.. warning::
   Importing some datasets with moving windows can cause vertical banding
   in the `xarray.Dataset`, which will affect the animation. The cause for
   this is unkown but can be circumvented by setting ``join = "override"``.

Customisation
-------------

The animation can be customised in much the same way as `xarray.DataArray.plot`,
see |animate_accessor| for more details. The coordinate units can be converted
before plotting as in :ref:`sec-unit-conversion`. Some functionality such as
``aspect`` and ``size`` are not fully implemented yet.

.. jupyter-execute::

   ds = sdfxr.open_mfdataset("tutorial_dataset_2d/*.sdf")

   # Change the units of the coordinates
   ds = ds.epoch.rescale_coords(1e6, "µm", ["X_Grid_mid", "Y_Grid_mid"])
   ds = ds.epoch.rescale_coords(1e15, "fs", ["time"])
   ds["time"].attrs["long_name"] = "t"

   # Change units and name of the variable
   da = ds["Derived_Number_Density_Electron"]
   da.data = da.values * 1e-6
   da.attrs["units"] = "cm$^{-3}$"
   da.attrs["long_name"] = "$n_e$"

   anim = da.epoch.animate(
      fps = 2,
      max_percentile = 95,
      title = "Target A",
      cmap = "plasma",
      )
   anim.show()

Advanced usage
--------------

Multiple plots on the same axes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is an example of how to combine multiple animations to plot on the same axis, 
this may become a more user-friendly function in a future update.

.. jupyter-execute::

   # Open the SDF files
   ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

   # Create figure and axes
   fig, ax = plt.subplots()
   plt.close(fig)

   # Generate the animations independently
   anim_1 = ds["Derived_Number_Density_Electron"].epoch.animate()
   anim_2 = ds["Derived_Number_Density_Ion"].epoch.animate()

   # Extract the update functions from the animations
   update_1 = anim_1._func
   update_2 = anim_2._func

   # Create axes details for new animation
   x_min, x_max = update_1(0)[0].axes.get_xlim()
   y_min_1, y_max_1 = update_1(0)[0].axes.get_ylim()
   y_min_2, y_max_2 = update_2(0)[0].axes.get_ylim()
   y_min = min(y_min_1, y_min_2)
   y_max = max(y_max_1, y_max_2)
   x_label = update_1(0)[0].axes.get_xlabel()
   y_label = "Number Density [m$^{-3}$]"
   label_1 = "Electron"
   label_2 = "Ion"

   # Create new update function
   def update_combined(frame):
      anim_1_fig = update_1(frame)[0]
      anim_2_fig = update_2(frame)[0]

      title = anim_1_fig.axes.title._text

      ax.clear()
      plot = ax.plot(anim_1_fig._x, anim_1_fig._y, label = label_1)
      ax.plot(anim_2_fig._x, anim_2_fig._y, label = label_2)
      ax.set_title(title)
      ax.set_xlim(x_min, x_max)
      ax.set_ylim(y_min, y_max)
      ax.set_xlabel(x_label)
      ax.set_ylabel(y_label)
      ax.legend(loc = "upper left")
      return plot

   N_frames = anim_1._save_count
   interval = anim_1._interval

   # Create combined animation
   anim_combined = FuncAnimation(
      fig,
      update_combined,
      frames=range(N_frames),
      interval = interval,
      repeat=True,
      )

   # Display animation as jshtml
   HTML(anim_combined.to_jshtml())