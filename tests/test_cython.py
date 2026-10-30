import numpy as np
import numpy.testing as npt
import pytest

from sdf_xarray import SDFFile, download

TEST_FILES_DIR = download.fetch_dataset("test_files_1D")


def test_sdffile():
    with SDFFile(str(TEST_FILES_DIR / "0000.sdf")) as f:
        assert f.header["filename"] == str(TEST_FILES_DIR / "0000.sdf")
        assert f.header["code_name"] == "Epoch1d"
        assert f.header["step"] == 0
        assert f.header["restart_flag"] is False

        assert f.run_info["version"] == "4.19.3"

        assert f.variables["Wall-time"].data == 0.014211990000000008


def test_sdffile_with_more_things():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        assert f.header["filename"] == str(TEST_FILES_DIR / "0010.sdf")
        assert f.header["code_name"] == "Epoch1d"
        assert f.header["step"] == 22105
        assert f.header["restart_flag"] is True

        assert f.run_info["version"] == "4.19.3"

        assert f.variables["Wall-time"].data == 4.068961859


def test_variable_names():
    with SDFFile(str(TEST_FILES_DIR / "0000.sdf")) as f:
        assert "Electric Field/Ex" in f.variables
        assert "grid" in f.grids
        assert "grid_mid" in f.grids


def test_manual_close():
    f = SDFFile(str(TEST_FILES_DIR / "0000.sdf"))
    f.close()

    f = SDFFile(str(TEST_FILES_DIR / "0010.sdf"))
    f.close()


def test_read_variable():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        ex = f.variables["Electric Field/Ex"].data
        dist_fn = f.variables["dist_fn/x_px/electron"].data

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


def test_read_grids():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        x_px = f.grids["grid/x_px/electron"].data

    assert len(x_px) == 2
    x, px = x_px

    expected_x = np.linspace(1.7252244667478382e-05, 0.0005348195846918299, 16)
    expected_px = np.linspace(-2.97e-22, 2.97e-22, 100)

    npt.assert_array_almost_equal(x, expected_x)
    npt.assert_array_almost_equal(px, expected_px)


def test_read_grid_mids():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        x_px = f.grids["grid/x_px/electron_mid"].data

    assert len(x_px) == 2
    x, px = x_px

    expected_x = np.linspace(3.45044893e-05, 5.17567340e-04, 15)
    expected_px = np.linspace(-2.94e-22, 2.94e-22, 99)

    npt.assert_array_almost_equal(x, expected_x)
    npt.assert_array_almost_equal(px, expected_px)


def test_cant_read_closed_file():
    f = SDFFile(str(TEST_FILES_DIR / "0000.sdf"))
    f.close()

    with pytest.raises(RuntimeError):
        f.variables["Electric Field/Ex"].data  # noqa: B018


if __name__ == "__main__":
    from pprint import pprint

    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        print("header")
        pprint(f.header)
        print("run_info")
        pprint(f.run_info)
        print("variables")
        pprint(f.variables)
        print("grids")
        pprint(f.grids)
        print("Ex")
        pprint(f.variables["Electric Field/Ex"].data)
        print("grid")
        pprint(f.grids["grid"].data)


def test_read_section_matches_full_read():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        dropped_key_affixes = ["cpu", "output file", "boundary"]
        variables = [
            v
            for v in f.variables.values()
            if getattr(v, "shape", ())
            and all(key not in v.name.lower() for key in dropped_key_affixes)
        ]
        assert any(v.is_point_data for v in variables)
        for var in variables:
            full = f.read(var)
            size = var.shape[-1]
            ranges = [(0, 0), (0, 1), (1, size), (size // 3, size // 2 + 1)]
            for start, stop in ranges:
                npt.assert_array_equal(
                    f.read(var, start, stop), full[..., start:stop], err_msg=var.name
                )
            # Reading a section must not affect later full reads
            npt.assert_array_equal(f.read(var), full, err_msg=var.name)


def test_read_section_out_of_range():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        var = f.variables["Electric Field/Ex"]
        with pytest.raises(IndexError):
            f.read(var, 0, var.shape[-1] + 1)


def test_read_mesh_component_matches_full_read():
    with SDFFile(str(TEST_FILES_DIR / "0010.sdf")) as f:
        meshes = [g for g in f.grids.values() if g.is_point_data]
        assert meshes
        for mesh in meshes:
            full = f.read(mesh)
            size = mesh.shape[0]
            for component in range(len(mesh.labels)):
                npt.assert_array_equal(
                    f.read_mesh_component(mesh, component), full[component]
                )
                npt.assert_array_equal(
                    f.read_mesh_component(mesh, component, 1, size // 2),
                    full[component][1 : size // 2],
                )
