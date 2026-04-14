from __future__ import annotations

from types import MethodType
from typing import TYPE_CHECKING

import xarray as xr
from xarray.plot.accessor import DataArrayPlotAccessor

from .plotting import animate, show

if TYPE_CHECKING:
    from matplotlib.animation import FuncAnimation

import numpy as np
from scipy.interpolate import RegularGridInterpolator
    
def resize_ndarray(
    arr: np.ndarray,
    new_shape: tuple | list | np.ndarray,
) -> np.ndarray:
    new_shape = list(new_shape)

    if arr.ndim != len(new_shape):
        raise ValueError("The number of dimensions in new_shape must match the input array.")

    old_grids = tuple(np.linspace(0, 1, size) for size in arr.shape)
    interpolator = RegularGridInterpolator(old_grids, arr, bounds_error=False, fill_value=0)  
    new_grids = tuple(np.linspace(0, 1, size) for size in new_shape)
    mesh = np.meshgrid(*new_grids, indexing='ij')
    coords = np.stack(mesh, axis=-1)
    output = interpolator(coords)

    return output

def resize_dataarray(
        da: xr.DataArray,
        new_shape: tuple | list | np.ndarray,
    ) -> xr.DataArray:

    resized_data = resize_ndarray(da.values, new_shape)

    da_resized = da.copy()

    da_resized = xr.DataArray(
        data=resized_data,
        dims=da.dims,
        attrs=da.attrs,
    )

    shape = da_resized.shape
    for i in range(len(da_resized.dims)):
        coord = list(da_resized.dims)[i]
        da_resized[coord] = resize_ndarray(da[coord], [shape[i]])
        da_resized[coord].attrs = da[coord].attrs
    
    da_resized.attrs["original_shape"] = da.shape

    return da_resized

@xr.register_dataarray_accessor("epoch")
class EpochAccessor:
    def __init__(self, xarray_obj: xr.DataArray):
        self._obj = xarray_obj

    def plot(self, *args, **kwargs) -> DataArrayPlotAccessor:
        """
        Builds upon `xarray.DataArray.plot` while changing some of its default behaviours.

        These changes are:

        - Flips the default axes order for 2D plots so that x and y are on the correct axes.
          This exists because plotting of 2D data in xarray uses the `xarray.plot.pcolormesh`
          function which takes assumes that ``x = dim[1]`` and ``y = dim[0]``.

        Parameters
        ----------
        args
            Positional arguments passed to `xarray.DataArray.plot`.
        kwargs
            Keyword arguments passed to `xarray.DataArray.plot`.
        """
        dims = self._obj.dims
        is_not_2d_data = len(dims) != 2
        is_time_dim_present = "time" in dims
        is_x_or_y_specified_in_kwargs = "x" in kwargs or "y" in kwargs

        if is_not_2d_data or is_time_dim_present or is_x_or_y_specified_in_kwargs:
            return self._obj.plot(*args, **kwargs)

        updated_kwargs = dict(kwargs)
        updated_kwargs.setdefault("x", dims[0])
        updated_kwargs.setdefault("y", dims[1])

        return self._obj.plot(*args, **updated_kwargs)

    def animate(self, *args, **kwargs) -> FuncAnimation:
        """Generate animations of Epoch data.

        Parameters
        ----------
        args
            Positional arguments passed to :func:`animation`.
        kwargs
            Keyword arguments passed to :func:`animation`.

        Examples
        --------
        >>> anim = ds["Electric_Field_Ey"].epoch.animate()
        >>> anim.save("animation.gif")
        >>> # Or in a jupyter notebook:
        >>> anim.show()
        """

        # Add anim.show() functionality
        # anim.show() will display the animation in a jupyter notebook
        anim = animate(self._obj, *args, **kwargs)
        anim.show = MethodType(show, anim)

        return anim
