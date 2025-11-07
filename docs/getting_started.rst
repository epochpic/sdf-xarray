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
   versions |python_versions_pypi|

Install sdf-xarray from PyPI with:

.. code-block:: bash

    pip install sdf-xarray

or download this code locally:

.. code-block:: bash

    git clone --recursive https://github.com/epochpic/sdf-xarray.git
    cd sdf-xarray
    pip install .

.. note::

   When loading SDF files, variables related to ``boundaries``, ``cpu`` and ``output file`` are excluded as they are problematic. If you wish to load these in please use the
   :ref:`loading-raw-files-getting-started` approach.

.. tip::

    All code examples throughout this documentation are visualised using Jupyter notebooks
    so that you can interactively explore `xarray.Dataset` objects. To do this on your machine
    make sure that you have the necessary dependencies installed: 

    .. code-block:: bash

        pip install "sdf-xarray[jupyter]"

Usage
-----

``sdf-xarray`` is a backend for xarray, and so is usable directly from
`xarray`. There are several ways to load SDF files:

- To load a single file, use `xarray.open_dataset`.
- To load multiple files, use `sdf_xarray.open_mfdataset` or `xarray.open_mfdataset`. 
- To access the raw contents of a single SDF file, use `sdf_xarray.sdf_interface.SDFFile`.

Loading single files
--------------------

.. jupyter-execute::

    import xarray as xr

    xr.open_dataset("tutorial_dataset_1d/0010.sdf")

Loading multiple files
----------------------

.. jupyter-execute::
    
    import sdf_xarray as sdfxr

    sdfxr.open_mfdataset("tutorial_dataset_1d/*.sdf")

.. _loading-raw-files-getting-started:

Loading raw files
-----------------

.. jupyter-execute::

    import sdf_xarray as sdfxr

    raw_ds = sdfxr.SDFFile("tutorial_dataset_1d/0010.sdf")
    raw_ds.variables.keys()
