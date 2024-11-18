.. container:: cell markdown

   .. rubric:: Key Functionalities of sdf-xarray
      :name: key-functionalities-of-sdf-xarray

   sdf-xarray provides a backend for `xarray <https://xarray.dev/>`__ to
   read SDF files as created by the
   `EPOCH <https://epochpic.github.io/>`__ plasma PIC code.

.. container:: cell code

   .. code:: python

      import xarray as xr
      from sdf_xarray import SDFPreprocess, SDFFile
      import matplotlib.pyplot as plt
      from IPython.display import display, HTML

      # Folders
      simulation_path_1d = "base_tutorial_dataset_1d"

.. container:: cell markdown

   .. rubric:: Loading SDF Files
      :name: loading-sdf-files

.. container:: cell markdown

   .. rubric:: Loading a Single SDF File
      :name: loading-a-single-sdf-file

.. container:: cell code

   .. code:: python

      xr.open_dataset(f"{simulation_path_1d}/0010.sdf")

   .. container:: output execute_result

      ::

         <xarray.Dataset> Size: 246kB
         Dimensions:                                       (X_Grid_mid: 1536,
                                                            X_Grid: 1537)
         Coordinates:
           * X_Grid                                        (X_Grid) float64 12kB -1e-0...
           * X_Grid_mid                                    (X_Grid_mid) float64 12kB -...
         Data variables: (12/27)
             Wall_time                                     float64 8B ...
             Electric_Field_Ex                             (X_Grid_mid) float64 12kB ...
             Electric_Field_Ey                             (X_Grid_mid) float64 12kB ...
             Electric_Field_Ez                             (X_Grid_mid) float64 12kB ...
             Magnetic_Field_Bx                             (X_Grid_mid) float64 12kB ...
             Magnetic_Field_By                             (X_Grid_mid) float64 12kB ...
             ...                                            ...
             Derived_Number_Density_Electron               (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Ion                    (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Photon                 (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Positron               (X_Grid_mid) float64 12kB ...
             Absorption_Total_Laser_Energy_Injected        float64 8B ...
             Absorption_Fraction_of_Laser_Energy_Absorbed  float64 8B ...
         Attributes: (12/21)
             filename:         base_tutorial_dataset_1d/0010.sdf
             file_version:     1
             file_revision:    4
             code_name:        Epoch1d
             step:             960
             time:             5.003461427972353e-14
             ...               ...
             compile_machine:  login1.viking2.yor.alces.network
             compile_flags:    unknown
             defines:          50364608
             compile_date:     Fri Oct 11 16:12:01 2024
             run_date:         Fri Oct 25 12:34:55 2024
             io_date:          Fri Oct 25 12:35:51 2024

.. container:: cell markdown

   .. rubric:: Loading a Single Raw SDF File
      :name: loading-a-single-raw-sdf-file

.. container:: cell code

   .. code:: python

      sdf_file = SDFFile(f"{simulation_path_1d}/0010.sdf")

      # You can access the variables of the SDF file as a dictionary
      # sdf_file.variables

      # With a little bit of HTML magic, we can display the variables in a nice way
      display(HTML("<br>".join([f"<span style='color:lightgreen'>{key}</span>: {value}" for key, value in sdf_file.variables.items()])))

   .. container:: output display_data

      ::

         <IPython.core.display.HTML object>

.. container:: cell markdown

   .. rubric:: Loading all SDF Files for a Simulation
      :name: loading-all-sdf-files-for-a-simulation

   When loading in all the files we have do some processing of the data
   so that we can correctly align it along the time dimension; This is
   done via the ``preprocess`` parameter.

.. container:: cell code

   .. code:: python

      xr.open_mfdataset(f"{simulation_path_1d}/*.sdf", preprocess=SDFPreprocess())

   .. container:: output execute_result

      ::

         <xarray.Dataset> Size: 10MB
         Dimensions:                                       (X_Grid: 1537,
                                                            X_Grid_mid: 1536, time: 41,
                                                            dim_laser_x_min_phase_0: 1,
                                                            dim_Random States_0: 384)
         Coordinates:
           * X_Grid                                        (X_Grid) float64 12kB -1e-0...
           * X_Grid_mid                                    (X_Grid_mid) float64 12kB -...
           * time                                          (time) float64 328B 2.606e-...
         Dimensions without coordinates: dim_laser_x_min_phase_0, dim_Random States_0
         Data variables: (12/40)
             Wall_time                                     (time) float64 328B 0.4287 ...
             Time_increment                                (time) float64 328B nan ......
             Plasma_frequency_timestep_restriction         (time) float64 328B nan ......
             Minimum_grid_position                         (time) float64 328B nan ......
             laser_x_min_phase                             (time, dim_laser_x_min_phase_0) float64 328B dask.array<chunksize=(1, 1), meta=np.ndarray>
             time_prev_normal                              (time) float64 328B nan ......
             ...                                            ...
             Derived_Number_Density_Electron               (time, X_Grid_mid) float64 504kB dask.array<chunksize=(1, 1536), meta=np.ndarray>
             Derived_Number_Density_Ion                    (time, X_Grid_mid) float64 504kB dask.array<chunksize=(1, 1536), meta=np.ndarray>
             Derived_Number_Density_Photon                 (time, X_Grid_mid) float64 504kB dask.array<chunksize=(1, 1536), meta=np.ndarray>
             Derived_Number_Density_Positron               (time, X_Grid_mid) float64 504kB dask.array<chunksize=(1, 1536), meta=np.ndarray>
             Absorption_Total_Laser_Energy_Injected        (time) float64 328B 9.081e+...
             Absorption_Fraction_of_Laser_Energy_Absorbed  (time) float64 328B 0.0 ......
         Attributes: (12/21)
             filename:         /Users/joel/Source/sdf-xarray/tutorials/base_tutorial_d...
             file_version:     1
             file_revision:    4
             code_name:        Epoch1d
             step:             3838
             time:             2.0003421833910338e-13
             ...               ...
             compile_machine:  login1.viking2.yor.alces.network
             compile_flags:    unknown
             defines:          50364608
             compile_date:     Fri Oct 11 16:12:01 2024
             run_date:         Fri Oct 25 12:34:55 2024
             io_date:          Fri Oct 25 12:40:14 2024

.. container:: cell markdown

   .. rubric:: Reading particle data
      :name: reading-particle-data

   By default, particle data isn't kept as it takes up a lot of space.
   Pass ``keep_particles=True`` as a keyword argument to
   ``open_dataset`` (for single files) or ``open_mfdataset`` (for
   multiple files)

.. container:: cell code

   .. code:: python

      xr.open_dataset(f"{simulation_path_1d}/0010.sdf", keep_particles=True)

   .. container:: output execute_result

      ::

         <xarray.Dataset> Size: 246kB
         Dimensions:                                       (X_Grid_mid: 1536,
                                                            X_Grid: 1537)
         Coordinates:
           * X_Grid                                        (X_Grid) float64 12kB -1e-0...
           * X_Grid_mid                                    (X_Grid_mid) float64 12kB -...
         Data variables: (12/27)
             Wall_time                                     float64 8B ...
             Electric_Field_Ex                             (X_Grid_mid) float64 12kB ...
             Electric_Field_Ey                             (X_Grid_mid) float64 12kB ...
             Electric_Field_Ez                             (X_Grid_mid) float64 12kB ...
             Magnetic_Field_Bx                             (X_Grid_mid) float64 12kB ...
             Magnetic_Field_By                             (X_Grid_mid) float64 12kB ...
             ...                                            ...
             Derived_Number_Density_Electron               (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Ion                    (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Photon                 (X_Grid_mid) float64 12kB ...
             Derived_Number_Density_Positron               (X_Grid_mid) float64 12kB ...
             Absorption_Total_Laser_Energy_Injected        float64 8B ...
             Absorption_Fraction_of_Laser_Energy_Absorbed  float64 8B ...
         Attributes: (12/21)
             filename:         base_tutorial_dataset_1d/0010.sdf
             file_version:     1
             file_revision:    4
             code_name:        Epoch1d
             step:             960
             time:             5.003461427972353e-14
             ...               ...
             compile_machine:  login1.viking2.yor.alces.network
             compile_flags:    unknown
             defines:          50364608
             compile_date:     Fri Oct 11 16:12:01 2024
             run_date:         Fri Oct 25 12:34:55 2024
             io_date:          Fri Oct 25 12:35:51 2024

.. container:: cell markdown

   .. rubric:: Data Interaction examples
      :name: data-interaction-examples

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

.. container:: cell code

   .. code:: python

      ds = xr.open_mfdataset(f"{simulation_path_1d}/*.sdf", preprocess=SDFPreprocess())

      ds["Electric_Field_Ex"]

   .. container:: output execute_result

      ::

         <xarray.DataArray 'Electric_Field_Ex' (time: 41, X_Grid_mid: 1536)> Size: 504kB
         dask.array<where, shape=(41, 1536), dtype=float64, chunksize=(1, 1536), chunktype=numpy.ndarray>
         Coordinates:
           * X_Grid_mid  (X_Grid_mid) float64 12kB -9.99e-06 -9.971e-06 ... 1.999e-05
           * time        (time) float64 328B 2.606e-17 5.003e-15 ... 1.95e-13 2e-13
         Attributes:
             units:       V/m
             point_data:  False
             full_name:   Electric Field/Ex

.. container:: cell markdown

   On top of accessing variables you can plot these ``xarray.Datasets``
   using the built-in ``plot()`` function (see
   https://docs.xarray.dev/en/stable/user-guide/plotting.html) which is
   a simple call to ``matplotlib``. This also means that you can access
   all the methods from ``matplotlib`` to manipulate your plot.

.. container:: cell code

   .. code:: python

      # This is discretized in both space and time
      ds["Electric_Field_Ex"].plot()
      plt.title("Electric Field along the x-axis")
      plt.show()

   .. container:: output display_data

      .. image:: images/electric_field_plot.png

.. container:: cell markdown

   After having loaded in a series of datasets we can select a
   simulation file by calling the ``.isel()`` function where we pass in
   the parameter of ``time=0`` where ``0`` can be a number between ``0``
   and the total number of simulation files.

   We can also use the ``.sel()`` function if we know the exact
   simulation time we want to select. There must be a corresponding
   dataset with this time for it work correctly.

.. container:: cell code

   .. code:: python

      print(f"There are a total of {ds["time"].size} time steps. (This is the same as the number of SDF files in the folder)")
      print("The time steps are: ")
      print(ds["time"].values)

      # The time at the 20th simulation step
      sim_time = ds['time'].isel(time=20).values
      print(f"The time at the 20th simulation step is {sim_time:.2e} s")

      # We can plot the time using either the isel or sel method passing in either the index or the value of the time
      ds["Electric_Field_Ex"].isel(time=20).plot()
      # ds["Electric_Field_Ex"].sel(time=sim_time).plot()
      plt.title(f"Electric Field along the x-axis at {sim_time:.2e} s")
      plt.show()

   .. container:: output stream stdout

      ::

         There are a total of 41 time steps. (This is the same as the number of SDF files in the folder)
         The time steps are: 
         [2.60596949e-17 5.00346143e-15 1.00069229e-14 1.50103843e-14
          2.00138457e-14 2.50173071e-14 3.00207686e-14 3.50242300e-14
          4.00276914e-14 4.50311529e-14 5.00346143e-14 5.50380757e-14
          6.00415371e-14 6.50449986e-14 7.00484600e-14 7.50519214e-14
          8.00032635e-14 8.50067249e-14 9.00101863e-14 9.50136477e-14
          1.00017109e-13 1.05020571e-13 1.10024032e-13 1.15027493e-13
          1.20030955e-13 1.25034416e-13 1.30037878e-13 1.35041339e-13
          1.40044801e-13 1.45048262e-13 1.50051723e-13 1.55003065e-13
          1.60006527e-13 1.65009988e-13 1.70013450e-13 1.75016911e-13
          1.80020373e-13 1.85023834e-13 1.90027295e-13 1.95030757e-13
          2.00034218e-13]
         The time at the 20th simulation step is 1.00e-13 s

   .. container:: output display_data

      .. image:: images/electric_field_plot_along_x.png

.. container:: cell markdown

   These datasets can also be easily manipulated the same way as you
   would with ``numpy`` arrays

.. container:: cell code

   .. code:: python

      ds["Laser_Absorption_Fraction_in_Simulation"] = (ds["Total_Particle_Energy_in_Simulation"] / ds["Absorption_Total_Laser_Energy_Injected"]) * 100
      # We can also manipulate the units and other attributes
      ds["Laser_Absorption_Fraction_in_Simulation"].attrs["units"] = "%"

      ds["Laser_Absorption_Fraction_in_Simulation"].plot()
      plt.title("Laser Absorption Fraction in Simulation")
      plt.show()

   .. container:: output display_data

      .. image:: images/laser_absorption.png

.. container:: cell markdown

   You can also call the ``plot()`` function on several variables with
   labels by delaying the call to ``plt.show()``

.. container:: cell code

   .. code:: python

      print(f"The total laser energy injected into the simulation is {ds["Absorption_Total_Laser_Energy_Injected"].max().values:.1e} J")
      print(f"The total particle energy absorbed by the simulation is {ds["Total_Particle_Energy_in_Simulation"].max().values:.1e} J")
      print(f"The laser absorption fraction in the simulation is {ds["Laser_Absorption_Fraction_in_Simulation"].max().values:.1f} %")
      ds["Total_Particle_Energy_Electron"].plot(label="Electron")
      ds["Total_Particle_Energy_Photon"].plot(label="Photon")
      ds["Total_Particle_Energy_Ion"].plot(label="Ion")
      ds["Total_Particle_Energy_Positron"].plot(label="Positron")
      plt.legend()
      plt.title("Particle Energy in Simulation per Species")
      plt.show()

   .. container:: output stream stdout

      ::

         The total laser energy injected into the simulation is 4.5e+12 J
         The total particle energy absorbed by the simulation is 3.0e+12 J
         The laser absorption fraction in the simulation is 66.0 %

   .. container:: output display_data

      .. image:: images/particle_energy_per_species.png
