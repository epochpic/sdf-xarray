import pathlib
import numpy as np
import numpy.testing as npt

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


def test_sdffile_with_more_things():
    with SDFFile(str(EXAMPLE_FILES_DIR / "0010.sdf")) as f:
        assert f.header["filename"] == str(EXAMPLE_FILES_DIR / "0010.sdf")
        assert f.header["code_name"] == "Epoch1d"
        assert f.header["step"] == 22105
        assert f.header["restart_flag"] is True

        assert f.run_info["version"] == "4.19.3"

        assert f.variables["Wall-time"].data == 3.968111756


def test_variable_names():
    with SDFFile(str(EXAMPLE_FILES_DIR / "0000.sdf")) as f:
        assert "Electric Field/Ex" in f.variables
        assert "grid" in f.grids
        assert "grid_mid" in f.grids


def test_manual_close():
    f = SDFFile(str(EXAMPLE_FILES_DIR / "0000.sdf"))
    f.close()

    f = SDFFile(str(EXAMPLE_FILES_DIR / "0010.sdf"))
    f.close()


def test_read_variable():
    with SDFFile(str(EXAMPLE_FILES_DIR / "0010.sdf")) as f:
        ex = f.read("Electric Field/Ex")
        dist_fn = f.read("dist_fn/x_px/electron")

    expected_ex = np.array(
        [
            -3126528.47057157754898071289062500000000,
            -3249643.37612255383282899856567382812500,
            -6827013.11566223856061697006225585937500,
            -9350267.99022011645138263702392578125000,
            -1643592.58487333403900265693664550781250,
            -2044751.41207189299166202545166015625000,
            -4342811.34666103497147560119628906250000,
            -10420841.38402196019887924194335937500000,
            -7038801.83154528774321079254150390625000,
            781649.31791684380732476711273193359375,
            4476555.84853181242942810058593750000000,
            5873312.79385650344192981719970703125000,
            -95930.60501570138148963451385498046875,
            -8977898.96547995693981647491455078125000,
            -7951712.64987809769809246063232421875000,
            -5655667.11171338520944118499755859375000,
        ]
    )

    # dist_fn[::4, ::20]
    expected_dist_fn = np.array(
        [
            [0.0, 0.0, 3.82999831618020078125e13, 0.0, 0.0],
            [0.0, 0.0, 1.1489994948540603125e14, 7.6599966323604015625e13, 0.0],
            [0.0, 0.0, 7.6599966323604e13, 3.8299983161802015625e13, 0.0],
            [0.0, 0.0, 3.82999831618020078125e13, 3.82999831618020078125e13, 0.0],
        ]
    )

    npt.assert_array_equal(ex, expected_ex)
    npt.assert_array_equal(dist_fn[::4, ::20], expected_dist_fn)


if __name__ == "__main__":
    from pprint import pprint

    with SDFFile(str(EXAMPLE_FILES_DIR / "0010.sdf")) as f:
        print("header")
        pprint(f.header)
        print("run_info")
        pprint(f.run_info)
        print("variables")
        pprint(f.variables)
        print("grids")
        pprint(f.grids)
        print("Ex")
        pprint(f.read("Electric Field/Ex"))
