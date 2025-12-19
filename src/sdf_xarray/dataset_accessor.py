from __future__ import annotations

from types import MethodType
from typing import TYPE_CHECKING

import xarray as xr

from .plotting import animate_multiple, show

if TYPE_CHECKING:
    from matplotlib.animation import FuncAnimation


@xr.register_dataset_accessor("epoch")
class EpochAccessor:
    def __init__(self, xarray_obj: xr.Dataset):
        # The xarray object is the Dataset, which we store as self._ds
        self._ds = xarray_obj

    def rescale_coords(
        self,
        multiplier: float,
        unit_label: str,
        coord_names: str | list[str],
    ) -> xr.Dataset:
        """
        Rescales specified X and Y coordinates in the Dataset by a given multiplier
        and updates the unit label attribute.

        Parameters
        ----------
        multiplier : float
            The factor by which to multiply the coordinate values (e.g., 1e6 for meters to microns).
        unit_label : str
            The new unit label for the coordinates (e.g., "µm").
        coord_names : str or list of str
            The name(s) of the coordinate variable(s) to rescale.
            If a string, only that coordinate is rescaled.
            If a list, all listed coordinates are rescaled.

        Returns
        -------
        xr.Dataset
            A new Dataset with the updated and rescaled coordinates.

        Examples
        --------
        # Convert X, Y, and Z from meters to microns
        >>> ds_in_microns = ds.epoch.rescale_coords(1e6, "µm", coord_names=["X_Grid", "Y_Grid", "Z_Grid"])

        # Convert only X to millimeters
        >>> ds_in_mm = ds.epoch.rescale_coords(1000, "mm", coord_names="X_Grid")
        """

        ds = self._ds
        new_coords = {}

        if isinstance(coord_names, str):
            # Convert single string to a list
            coords_to_process = [coord_names]
        elif isinstance(coord_names, list):
            # Use the provided list
            coords_to_process = coord_names
        else:
            coords_to_process = list(coord_names)

        for coord_name in coords_to_process:
            if coord_name not in ds.coords:
                raise ValueError(
                    f"Coordinate '{coord_name}' not found in the Dataset. Cannot rescale."
                )

            coord_original = ds[coord_name]

            coord_rescaled = coord_original * multiplier
            coord_rescaled.attrs = coord_original.attrs.copy()
            coord_rescaled.attrs["units"] = unit_label

            new_coords[coord_name] = coord_rescaled

        return ds.assign_coords(new_coords)

    def animate_multiple(
        self,
        *variables: str | xr.DataArray,
        datasets_kwargs: list[dict] | None = None,
        **kwargs,
    ) -> FuncAnimation:
        """
        Animate multiple Dataset variables on the same axes.

        Parameters
        ----------
        variables
            The variables to animate.
        datasets_kwargs
            Per-dataset keyword arguments passed to plotting.
        kwargs
            Common keyword arguments forwarded to animation.

        Examples
        --------
        >>> anim = ds.epoch.animate_multiple(
                ds["Derived_Number_Density_Electron"],
                ds["Derived_Number_Density_Ion"],
                datasets_kwargs=[{"label": "Electron"}, {"label": "Ion"}],
                ylabel="Derived Number Density [1/m$^3$]"
            )
        >>> anim.save("animation.gif")
        >>> # Or in a jupyter notebook:
        >>> anim.show()
        """

        dataarrays = [
            self._obj[var] if isinstance(var, str) else var for var in variables
        ]
        anim = animate_multiple(
            *dataarrays,
            datasets_kwargs=datasets_kwargs,
            **kwargs,
        )
        anim.show = MethodType(show, anim)

        return anim
