from __future__ import annotations

from types import MethodType
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr
from xarray.plot.accessor import DataArrayPlotAccessor

from .plotting import animate, show

if TYPE_CHECKING:
    from matplotlib.animation import FuncAnimation


def _resize_ndarray(
    arr: np.ndarray,
    new_shape: tuple | list | np.ndarray,
) -> np.ndarray:
    """
    Resizes a `numpy.ndarray` to another shape. The returned array must have the
    same dimensionality as the input array.

    Parameters
    ----------
    arr
        The input array.
    new_shape
        The shape of the new `xarray.DataArray`, must be the same length as arr.shape.
    """

    from scipy.interpolate import RegularGridInterpolator  # noqa: PLC0415

    if arr.ndim != len(new_shape):
        raise ValueError(
            f"The number of dimensions must match the input array. (original: {arr.ndim}, new: {len(new_shape)})"
        )

    old_grids = tuple(np.linspace(0, 1, size) for size in arr.shape)
    new_grids = tuple(np.linspace(0, 1, size) for size in new_shape)
    mesh = np.meshgrid(*new_grids, indexing="ij")
    coords = np.stack(mesh, axis=-1)

    return RegularGridInterpolator(old_grids, arr, bounds_error=False, fill_value=0)(
        coords
    )


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

    def resize(
        self,
        new_shape: tuple | list | np.ndarray,
    ) -> xr.DataArray:
        """
        Resizes a `xarray.DataArray` to another shape. The returned array must have the
        same dimensionality as the input array.

        Parameters
        ----------
        new_shape
            The shape of the new `xarray.DataArray`, must be the same length as self.shape.
        """

        da = self._obj
        # Create a copy of the existing dataarray so that we can copy over the
        # original dims, attrs and shape
        da_resized = da.copy()

        # Resize the dataarray's data, either via upsampling or downsampling
        resized_data = _resize_ndarray(da.values, new_shape)

        da_resized = xr.DataArray(
            data=resized_data,
            dims=da.dims,
            attrs=da.attrs,
        )
        # Add a new attr containing the original shape
        da_resized.attrs["original_shape"] = da.shape

        # Resize the dataarray's underlying dimensions with their new shapes
        for coord_name, shape in zip(da_resized.dims, da_resized.shape):
            da_resized[coord_name] = _resize_ndarray(da[coord_name], [shape])
            da_resized[coord_name].attrs = da[coord_name].attrs

        return da_resized
