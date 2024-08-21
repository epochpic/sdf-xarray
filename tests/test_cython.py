import pathlib

from sdf_xarray import SDFFile

EXAMPLE_FILES_DIR = pathlib.Path(__file__).parent / "example_files"


def test_sdffile():
    with SDFFile(str(EXAMPLE_FILES_DIR / "0000.sdf")) as f:
        assert f.header["filename"] == str(EXAMPLE_FILES_DIR / "0000.sdf")
        assert f.header["code_name"] == "Epoch1d"
        assert f.header["step"] == 0
        assert f.header["restart_flag"] is False

        assert f.run_info["version"] == "4.19.3"

        assert f.variables["Wall-time"].data == 0.0032005560000000002


def test_variable_names():
    with SDFFile(str(EXAMPLE_FILES_DIR / "0000.sdf")) as f:
        names = f.variables

    assert "Electric Field/Ex" in names
    assert "Grid/Grid" in names


if __name__ == "__main__":
    with SDFFile(str(EXAMPLE_FILES_DIR / "0000.sdf")) as f:
        print(f.header)
        print(f.run_info)
        print(f.variables)
