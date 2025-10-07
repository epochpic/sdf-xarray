.. _sec-getting-started:

=================
 Getting Started
=================

Installation
------------

.. |python_versions_pypi| image:: https://img.shields.io/pypi/pyversions/sdf-xarray.svg
   :alt: Supported Python versions
   :target: https://pypi.org/project/sdf-xarray/

.. important::

   To install this package, ensure that you are using one of the supported Python
   versions: |python_versions_pypi|

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
- To load multiple files, use :func:`xarray.open_mfdataset` or :func:`sdf_xarray.open_mfdataset` (Recommended). 
- To access the raw contents of a single SDF file, use :func:`sdf_xarray.sdf_interface.SDFFile`.

.. note::
   When loading ``*.sdf`` files, variables related to ``boundaries``, ``cpu`` and ``output file`` are excluded as they are problematic.

Single file loading
~~~~~~~~~~~~~~~~~~~

Basic usage:

.. ipython:: python

    import xarray as xr
    import sdf_xarray as sdfxr
    with xr.open_dataset("tutorial_dataset_1d/0010.sdf") as df:
        print(df["Electric_Field_Ex"])

Multi file loading
~~~~~~~~~~~~~~~~~~

To open a whole simulation's files at once use the :func:`sdf_xarray.open_mfdataset` function:

.. ipython:: python
    
    sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

You can alternatively open the dataset using the xarray's :func:`xarray.open_mfdataset`
along with the ``preprocess=sdfxr.SDFPreprocess()``:

.. ipython:: python

    xr.open_mfdataset(
        "tutorial_dataset_1d/*.sdf",
        join="outer",
        compat="no_conflicts",
        preprocess=sdfxr.SDFPreprocess()
    )

:class:`sdf_xarray.SDFPreprocess` checks that all the files are from the same simulation, and
ensures there's a ``time`` dimension so the files are correctly concatenated.

If your simulation has multiple ``output`` blocks so that not all variables are
output at every time step, then those variables will have ``NaN`` values at the
corresponding time points.

Alternatively, we can create a separate time dimensions for each ``output``
block using :func:`sdf_xarray.open_mfdataset` with ``separate_times=True``:

.. ipython:: python

    sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf", separate_times=True)

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
