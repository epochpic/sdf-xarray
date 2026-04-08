# Why use sdf-xarray?

`sdf_xarray` is a Python package that allows you to load [EPOCH SDF files](https://epochpic.github.io/documentation/visualising_output.html) into structured N-D labelled datasets (<inv:#xarray>). We leverage the underlying [`SDF-C`](https://github.com/epochpic/SDF_C) library to convert the binary SDF files to <inv:#xarray.Dataset>. This package might not work as expected when loading datasets so please check the <project:known_issues.md> page first before raising a [GitHub Issue](https://github.com/epochpic/sdf-xarray/issues/new).

There are several benefits to using this package over the [`sdf_helper`](https://epochpic.github.io/documentation/visualising_output/python_sdf_helper.html) including:

- [data to numpy and pandas](https://docs.xarray.dev/en/stable/user-guide/pandas.html) - Data can be easily converted to [numpy](https://www.numpy.org/) or [pandas](https://pandas.pydata.org/) if you prefer to work with raw data.
- [data labelling](project:understanding_datasets.md) - All SDF files come with a bunch of information about them such as the `dimensions`, `units` and `name` of the variable. In <inv:#xarray> these are added to each variable making it much easier to read.
- [lazy/partial loading](https://docs.xarray.dev/en/stable/internals/internal-design.html#lazy-loading) - This reduces the RAM requirements when loading large SDF files as we only load the actual array values when they are needed.
- [plotting](project:understanding_datasets.md#plotting) - You can easily plot variables across several dimensions including time using built in <inv:#matplotlib> support.
- [animating](project:animation.md) - Visualise your data across time or slice through another dimension and make beautiful GIFs for your presentations.
- [deck loading](loading-input-deck) - <project:#sdf_xarray> automatically loads in the associated `input.deck` utilised when creating the simulation so that you can access setup variables.
- [easier unit conversion](project:unit_conversion.md) - Convert dimensions and variable units to other types with the help of [`pint`](https://pint.readthedocs.io/en/stable).
