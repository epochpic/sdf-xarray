.. _sec-getting-started:

=================
 Getting Started
=================

Installation
------------

Install sdf-xarray from PyPI with:

.. code-block:: bash

    pip install sdf-xarray

or from a local checkout:

.. code-block:: bash

    git clone https://github.com/epochpic/sdf-xarray.git
    cd sdf-xarray
    pip install .

Usage
-----

``sdf-xarray`` is a backend for xarray, and so is usable directly from
`xarray`. There are several ways to load SDF files:

- To load a single file, use :func:`xarray.open_dataset`.
- To load multiple files, use :func:`xarray.open_mfdataset` or :func:`sdf_xarray.open_mfdataset`.
- To access the raw contents of a single SDF file, use :func:`sdf_xarray.sdf_interface.SDFFile`.

.. note::
   When loading ``*.sdf`` files, variables related to ``boundaries``, ``cpu`` and ``output file`` are excluded as they are problematic.

Single file loading
~~~~~~~~~~~~~~~~~~~

Basic usage:

.. ipython:: python

    import xarray as xr
    with xr.open_dataset("tutorial_dataset_1d/0010.sdf") as df:
        print(df["Electric_Field_Ex"])

Multi file loading
~~~~~~~~~~~~~~~~~~

To open a whole simulation at once, pass
``preprocess=sdf_xarray.SDFPreprocess()`` to `xarray.open_mfdataset`:

.. ipython:: python

    from sdf_xarray import SDFPreprocess
    xr.open_mfdataset("tutorial_dataset_1d/*.sdf", preprocess=SDFPreprocess())

`SDFPreprocess` checks that all the files are from the same simulation, and
ensures there's a ``time`` dimension so the files are correctly concatenated.

If your simulation has multiple ``output`` blocks so that not all variables are
output at every time step, then those variables will have ``NaN`` values at the
corresponding time points.

Alternatively, we can create a separate time dimensions for each ``output``
block using `sdf_xarray.open_mfdataset` with ``separate_times=True``:

.. ipython:: python

    from sdf_xarray import open_mfdataset
    open_mfdataset("tutorial_dataset_1d/*.sdf", separate_times=True)

This is better for memory consumption, at the cost of perhaps slightly less
friendly comparisons between variables on different time coordinates.

Reading particle data
~~~~~~~~~~~~~~~~~~~~~

By default, particle data isn't kept as it takes up a lot of space. Pass
``keep_particles=True`` as a keyword argument to `open_dataset` (for single files)
or `open_mfdataset` (for multiple files):

.. ipython:: python

    xr.open_dataset("tutorial_dataset_1d/0010.sdf", keep_particles=True)

Loading SDF files directly
~~~~~~~~~~~~~~~~~~~~~~~~~~

For debugging, sometimes it's useful to see the raw SDF files:

.. ipython:: python

    from sdf_xarray import SDFFile
    with SDFFile("tutorial_dataset_1d/0010.sdf") as sdf_file:
        print(sdf_file.variables["Electric Field/Ex"])
