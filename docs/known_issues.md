# Known Issues

There are a couple of known 'quirks' in `sdf_xarray`:

- [Issue #57](https://github.com/epochpic/sdf-xarray/issues/57) Loading multiple
SDF files with <project:#sdf_xarray.open_mfdataset> can lead to out-of-memory
errors. The issue is believed to stem from how the underlying <inv:#xarray> library
handles coordinates, causing it to infer an excessively large array shape that
requests far more memory than is needed. Due to the significant architectural
changes required for a fix, the maintainers do not plan to resolve this. The
recommended solution is to load the files individually or in smaller batches.
