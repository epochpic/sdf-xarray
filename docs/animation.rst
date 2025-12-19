.. _sec-animation:

.. |animate_accessor| replace:: `xarray.DataArray.epoch.animate
   <sdf_xarray.plotting.animate>`

.. |animate_multiple_accessor| replace:: `xarray.Dataset.epoch.animate_multiple
   <sdf_xarray.plotting.animate_multiple>`

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
   
   # Access a DataArray within the Dataset
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

   It can also be viewed from a Python interpreter with:

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
return a `xarray.plot.hist`. However, this may not be
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
(changing x-axis over time). |animate_accessor| can accept the boolean parameter
``move_window`` and change the x-axis limits accordingly.

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
   anim = da.epoch.animate(move_window=True, fps = 5)
   anim.show()

.. warning::
   Importing some datasets with moving windows can cause vertical banding
   in the `xarray.Dataset`, which will affect the animation. The cause for
   this is unknown but can be circumvented by setting ``join = "override"``.

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

Combining multiple animations
-----------------------------

|animate_multiple_accessor| creates a `matplotlib.animation.FuncAnimation`
that contains multiple plots layered on top of each other.

1D simulation
~~~~~~~~~~~~~

What follows is an example of how to combine multiple animations on the
same axis.

.. jupyter-execute::

   ds = sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

   anim = ds.epoch.animate_multiple(
      ds["Derived_Number_Density_Electron"],
      ds["Derived_Number_Density_Ion"],
      datasets_kwargs=[{"label": "Electron"}, {"label": "Ion"}],
      ylim=(0e27,4e27),
      ylabel="Derived Number Density [1/m$^3$]"
   )

   anim.show()

2D simulation
~~~~~~~~~~~~~

.. tip::
   To correctly display 2D data on top of one another you need to specify
   the ``alpha`` value which sets the opacity of the plot.

This also works with 2 dimensional data.

.. jupyter-execute::
   
   import numpy as np
   from matplotlib.colors import LogNorm

   ds = sdfxr.open_mfdataset("tutorial_dataset_2d/*.sdf")

   flux_magnitude = np.sqrt(
      ds["Derived_Poynting_Flux_x"]**2 +
      ds["Derived_Poynting_Flux_y"]**2 +
      ds["Derived_Poynting_Flux_z"]**2
   )
   flux_magnitude.attrs["long_name"] = "Poynting Flux Magnitude"
   flux_magnitude.attrs["units"] = "W/m$^2$"

   # Cut-off low energy values so that they will be rendered as transparent
   # in the plot as they've been set to NaN
   flux_masked = flux_magnitude.where(flux_magnitude > 0.2e23)
   flux_norm = LogNorm(
      vmin=float(flux_masked.min()),
      vmax=float(flux_masked.max())
   )

   anim = ds.epoch.animate_multiple(
      ds["Derived_Number_Density_Electron"],
      flux_masked,
      datasets_kwargs=[
         {"alpha": 1.0},
         {"cmap": "hot", "norm": flux_norm, "alpha": 0.9},
      ],
   )
   anim.show()