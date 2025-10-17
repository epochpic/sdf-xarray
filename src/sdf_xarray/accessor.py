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
        x_coord_name: str = "X_Grid_mid",
        y_coord_name: str = "Y_Grid_mid",
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
        x_coord_name : str, optional
            The name of the X coordinate variable. Defaults to "X_Grid_mid".
        y_coord_name : str, optional
            The name of the Y coordinate variable. Defaults to "Y_Grid_mid".

        Returns
        -------
        xr.Dataset
            A new Dataset with the updated and rescaled coordinates.

        Examples
        --------
        # Convert from meters to microns (multiplier=1e6, unit_label="µm")
        >>> ds_in_microns = ds.epoch.rescale_coords(1e6, "µm")

        # Convert from meters to centimeters (multiplier=100, unit_label="cm")
        >>> ds_in_cm = ds.epoch.rescale_coords(100, "cm", x_coord_name="X", y_coord_name="Y")
        """

        ds = self._ds
        new_coords = {}

        if x_coord_name not in ds.coords:
            raise ValueError(
                f"X coordinate '{x_coord_name}' not found in the Dataset. Cannot rescale."
            )
        x_coord_original = ds[x_coord_name]

        x_coord_rescaled = x_coord_original * multiplier
        x_coord_rescaled.attrs = x_coord_original.attrs.copy()
        x_coord_rescaled.attrs["units"] = unit_label

        new_coords[x_coord_name] = x_coord_rescaled

        if y_coord_name not in ds.coords:
            raise ValueError(
                f"Y coordinate '{y_coord_name}' not found in the Dataset. Cannot rescale."
            )

        y_coord_original = ds[y_coord_name]

        y_coord_rescaled = y_coord_original * multiplier
        y_coord_rescaled.attrs = y_coord_original.attrs.copy()
        y_coord_rescaled.attrs["units"] = unit_label

        new_coords[y_coord_name] = y_coord_rescaled

        return ds.assign_coords(new_coords)
