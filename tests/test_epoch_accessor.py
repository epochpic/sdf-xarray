import pathlib
import tempfile

import matplotlib as mpl
import pytest
import xarray as xr
from matplotlib.animation import PillowWriter

from sdf_xarray import SDFPreprocess

mpl.use("Agg")

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"


def test_animation_accessor():
    array = xr.DataArray(
        [1, 2, 3],
        dims=["x"],
        coords={"x": [0, 1, 2]},
        attrs={"long_name": "Test Array", "units": "m"},
    )
    assert hasattr(array, "epoch")
    assert hasattr(array.epoch, "animate")


def test_animate_headless():
    with xr.open_mfdataset(
        EXAMPLE_FILES_DIR.glob("*.sdf"), preprocess=SDFPreprocess()
    ) as ds:
        anim = ds["Derived_Number_Density_electron"].epoch.animate()

        # Specify a custom writable temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/output.gif"
            try:
                anim.save(temp_file_path, writer=PillowWriter(fps=2))
            except Exception as e:
                pytest.fail(f"animate().save() failed in headless mode: {e}")
