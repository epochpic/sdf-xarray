from __future__ import annotations

from types import MethodType
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr
from xarray.plot.accessor import DataArrayPlotAccessor

from .plotting import _recover_vertex_coord, animate, show, voxel_plot

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

        if len(dims) == 1:
            return self._obj.plot(*args, **kwargs)

        if len(dims) == 2:
            updated_kwargs = dict(kwargs)
            updated_kwargs.setdefault("x", dims[0])
            updated_kwargs.setdefault("y", dims[1])
            return self._obj.plot(*args, **updated_kwargs)

        if len(dims) == 3:
            return voxel_plot(self._obj, *args, **kwargs)

        return self._obj.plot(*args, **kwargs)

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
        new_shape,
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

        # Create resized data and Dataset
        data_resized = _resize_ndarray(da.values, new_shape)
        da_resized = da.copy()
        da_resized = xr.DataArray(
            data=data_resized,
            dims=da.dims,
            attrs=da.attrs,
        )

        original_cell_size_da = []

        # Resize coordinates and add to DataArray
        for i in range(len(da_resized.dims)):
            coord = list(da_resized.dims)[i]

            if coord[-4:] == "_mid":
                # If the coordinate is a midpoint coordinate, care must be taken to resize correctly
                vertex_coord = _recover_vertex_coord(da[coord])
                vertex_coord_resized = np.linspace(
                    vertex_coord[0], vertex_coord[-1], new_shape[i] + 1
                )
                # Turn the vertex coord back into a midpoint coord
                da_resized[coord] = (
                    (np.roll(vertex_coord_resized, 1) + vertex_coord_resized) / 2
                )[1:]
            else:
                # If not, the coordinate can be simply resized
                coord_min = da[coord][0].values
                coord_max = da[coord][-1].values
                da_resized[coord] = np.linspace(coord_min, coord_max, new_shape[i])

            da_resized[coord].attrs = da[coord].attrs

            # Add original information as attributes
            if "original_shape" not in da.attrs:
                da_resized[coord].attrs["original_size"] = da.shape[i]
                original_cell_size = float((da[coord][1] - da[coord][0]).values)
                original_cell_size_da.append(original_cell_size)
                da_resized[coord].attrs["original_cell_size"] = original_cell_size

        if "original_shape" not in da.attrs:
            da_resized.attrs["original_shape"] = da.shape
            da_resized.attrs["original_cell_size"] = tuple(original_cell_size_da)

        return da_resized

    def limit(
        self,
        limits,
        drop: bool = True,
    ) -> xr.DataArray:
        """
        Drops values outside the specified limits.

        Parameters
        ----------
        limits
            Array-like list of limits.
        drop
            Bool specifying whether to drop the co-ordinates outside the limits (default = True).
        """
        da = self._obj
        limits = list(limits)

        # List of dimension names
        dims = da.dims

        original_lims_da = []
        for i in range(len(dims)):
            limits[i] = list(limits[i])

            # Find the original limits of the dataarray
            original_lims = (
                float(da[dims[i]].values[0]),
                float(da[dims[i]].values[-1]),
            )
            original_lims_da.append(original_lims)
            if "original_lims" not in da[dims[i]].attrs:
                da[dims[i]].attrs["original_lims"] = original_lims

            # If None is passed into limit, will assume the existing limit
            if limits[i][0] is None:
                limits[i][0] = original_lims[0]
            if limits[i][-1] is None:
                limits[i][-1] = original_lims[1]

            # Limit dataarray
            da = da.where(da[dims[i]] >= limits[i][0], drop=drop).where(
                da[dims[i]] <= limits[i][1], drop=drop
            )

        if "original_lims" not in da.attrs:
            da.attrs["original_lims"] = tuple(original_lims_da)

        return da
