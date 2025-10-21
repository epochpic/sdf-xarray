from typing import Union

import xarray as xr


@xr.register_dataset_accessor("epoch")
class EpochAccessor:
    def __init__(self, xarray_obj: xr.Dataset):
        # The xarray object is the Dataset, which we store as self._ds
        self._ds = xarray_obj

    def rescale_coords(
        self,
        multiplier: float,
        unit_label: str,
        coord_names: Union[str, list[str]],
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
            raise TypeError("`coord_names` must be a string or a list of strings.")

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
