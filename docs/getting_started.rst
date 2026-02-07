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


Interaction
-----------

There are two main ways to load EPOCH SDF files into xarray objects: using the dedicated
`sdf_xarray` functions or using the standard `xarray` interface with our custom engine.
For examples of how to use these functions see :ref:`loading-sdf-files`.

All code examples throughout this documentation are visualised using Jupyter notebooks
so that you can interactively explore the datasets. To do this on your machine make
sure that you have the necessary dependencies installed: 

.. code-block:: bash

    pip install "sdf-xarray[jupyter]"

.. important::
   
   When loading SDF files, variables related to ``boundaries``, ``cpu`` and ``output file``
   are excluded as they are problematic. If you wish to load these variables in see
   :ref:`loading-raw-files`.


Using sdf_xarray (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These functions are wrappers designed specifically for SDF data, providing the most
straightforward experience:

- **Single files**: Use `sdf_xarray.open_dataset` or `sdf_xarray.open_datatree`
- **Multiple files**: Use `sdf_xarray.open_mfdataset` or `sdf_xarray.open_mfdatatree`
- **Raw files**: use `sdf_xarray.sdf_interface.SDFFile`

Using xarray
~~~~~~~~~~~~

If you prefer using the native `xarray` functions, you can use the `xarray.open_dataset`,
`xarray.open_datatree` and `xarray.open_mfdataset`. Strangely there is no function in
`xarray` for ``xarray.open_mfdatatree``.

These functions should all work out of the box as long as `sdf_xarray` is installed on your
system, if you are having issues with it reading files, you might need to pass the parameter
``engine=sdf_engine`` when calling any of the above xarray functions.
