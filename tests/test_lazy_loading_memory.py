"""Compare opening memory with the pre-fix backend in fresh Linux processes.

Run with ``pytest -s tests/test_lazy_loading_memory.py`` to display the results.
The generated SDF contains one 64 MiB field and small coordinates. The baseline
uses the actual Python backend from commit 65bb865; both processes use the same
installed Cython/SDF-C reader, which was unchanged by the lazy-loading fix.
No simulation data, extra dependencies or historical package build are needed.
"""

import argparse
import gc
import json
import os
import shutil
import struct
import subprocess
import sys
import types
from pathlib import Path

import pytest

_MIB = 1024**2
_FILE_HEADER = struct.Struct("<4siii32sqqiiiidiiii3B5x")
_BLOCK_HEADER = struct.Struct("<qq32sqiii64si")


def _write_sdf(path, shape):
    """Write a minimal SDF 1.4 file with run info, a mesh and a cell field.

    Layouts follow SDF-C's sdf_read_header(), sdf_read_next_block_header(),
    sdf_read_run_info(), sdf_read_plain_mesh_info() and
    sdf_read_plain_variable_info(). Payloads are written in bounded chunks.
    """
    nx, ny = shape
    run_info = struct.pack(
        "<ii64s64s64s64sqiiii",
        4,
        19,
        b"synthetic",
        b"synthetic",
        b"memory test",
        b"",
        0,
        0,
        0,
        0,
        0,
    )
    mesh_info = struct.pack(
        "<2d32s32s32s32si4d2i",
        1.0,
        1.0,
        b"X",
        b"Y",
        b"m",
        b"m",
        1,
        0.0,
        0.0,
        nx,
        ny,
        nx + 1,
        ny + 1,
    )
    mesh_data = b"".join(
        struct.pack(f"<{size + 1}d", *range(size + 1)) for size in shape
    )
    field_info = struct.pack("<d32s32s2ii", 1.0, b"V/m", b"grid", nx, ny, 0)
    field_bytes = nx * ny * 8
    # (id, name, block type, datatype, dimensions, metadata, payload length)
    blocks = [
        (b"run", b"Run info", 7, 0, 1, run_info, 0),
        (b"grid", b"Grid/Grid", 1, 4, 2, mesh_info, len(mesh_data)),
        (b"ex", b"Electric Field/Ex", 3, 4, 2, field_info, field_bytes),
    ]
    data_location = _FILE_HEADER.size + sum(
        _BLOCK_HEADER.size + len(block[5]) for block in blocks
    )
    with path.open("wb") as stream:
        stream.write(
            _FILE_HEADER.pack(
                b"SDF1",
                0x01020E0F,
                1,
                4,
                b"Epoch2d",
                _FILE_HEADER.size,
                0,
                0,
                len(blocks),
                _BLOCK_HEADER.size,
                0,
                0.0,
                1,
                1,
                64,
                1,
                0,
                0,
                0,
            )
        )
        block_location = _FILE_HEADER.size
        for block_id, name, block_type, dtype, ndims, info, data_bytes in blocks:
            block_location += _BLOCK_HEADER.size + len(info)
            stream.write(
                _BLOCK_HEADER.pack(
                    block_location,
                    data_location,
                    block_id,
                    data_bytes,
                    block_type,
                    dtype,
                    ndims,
                    name,
                    len(info),
                )
            )
            stream.write(info)
            data_location += data_bytes
        stream.write(mesh_data)
        chunk = struct.pack("<d", 1.0) * (_MIB // 8)
        remaining = field_bytes
        while remaining:
            size = min(remaining, len(chunk))
            stream.write(chunk[:size])
            remaining -= size


def _resident_bytes():
    """Include native buffers by measuring resident process pages, not Python allocations."""
    pages = int(Path("/proc/self/statm").read_text().split()[1])
    return pages * os.sysconf("SC_PAGE_SIZE")


def _measure(path, warmup, backend_source=None):
    import numpy as np  # noqa: PLC0415
    import xarray as xr  # noqa: PLC0415

    import sdf_xarray as backend  # noqa: PLC0415

    if backend_source is not None:
        baseline = types.ModuleType("sdf_xarray._memory_baseline")
        baseline.__package__ = "sdf_xarray"
        baseline.__file__ = str(backend_source)
        sys.modules[baseline.__name__] = baseline
        exec(
            compile(backend_source.read_text(), str(backend_source), "exec"),
            baseline.__dict__,
        )
        backend = baseline

    # Warm imports and the native reader before recording the baseline.
    with xr.open_dataset(warmup, engine=backend.SDFEntrypoint) as dataset:
        dataset.load()
    gc.collect()
    baseline_bytes = _resident_bytes()
    with xr.open_dataset(path, engine=backend.SDFEntrypoint) as dataset:
        field = dataset["Electric_Field_Ex"]
        assert field.shape == (2048, 4096)
        opened_bytes = _resident_bytes()
        # Hold the result while measuring: even this small slice loads the
        # complete block and retains its backing NumPy array.
        values = field.isel(X_Grid_mid=slice(0, 2), Y_Grid_mid=slice(0, 2)).values
        np.testing.assert_array_equal(values, np.ones((2, 2)))
        accessed_bytes = _resident_bytes()
    return {
        "baseline_bytes": baseline_bytes,
        "opened_bytes": opened_bytes,
        "accessed_bytes": accessed_bytes,
        "open_growth_bytes": opened_bytes - baseline_bytes,
        "access_growth_bytes": accessed_bytes - baseline_bytes,
    }


def _run_worker(path, warmup, backend_source=None):
    command = [sys.executable, str(Path(__file__).resolve()), str(path), str(warmup)]
    if backend_source is not None:
        command.extend(["--backend-source", str(backend_source)])
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return json.loads(result.stdout)


@pytest.mark.skipif(sys.platform != "linux", reason="RSS measurement uses Linux /proc")
def test_memory_before_and_after_lazy_loading_fix(tmp_path):
    """Opening should avoid allocating a field, while accessing it still loads it."""
    if shutil.which("git") is None:
        pytest.skip("Historical comparison requires Git and the pre-fix commit")
    repo = Path(__file__).resolve().parents[1]
    source = subprocess.run(
        ["git", "-C", str(repo), "show", "65bb865:src/sdf_xarray/__init__.py"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if source.returncode:
        pytest.skip(
            "Pre-fix commit 65bb865 is unavailable (e.g. a wheel or shallow clone)"
        )
    before_source = tmp_path / "before_fix.py"
    before_source.write_text(source.stdout)
    path = tmp_path / "memory.sdf"
    warmup = tmp_path / "warmup.sdf"
    _write_sdf(path, (2048, 4096))
    _write_sdf(warmup, (2, 2))
    before = _run_worker(path, warmup, before_source)
    after = _run_worker(path, warmup)

    print("\nResident memory growth above the warmed process baseline (MiB):")
    print("Backend             After opening     After accessing a slice")
    for name, measurements in [("Before fix", before), ("After fix", after)]:
        print(
            f"{name:<20}{measurements['open_growth_bytes'] / _MIB:>9.2f}"
            f"{measurements['access_growth_bytes'] / _MIB:>28.2f}"
        )
    # Broad bounds tolerate allocator/platform variation while detecting the
    # regression: eagerly opening must retain the native 64 MiB field buffer.
    payload_bytes = 64 * _MIB
    assert before["open_growth_bytes"] > payload_bytes * 0.75
    assert after["open_growth_bytes"] < payload_bytes * 0.5
    assert (
        before["open_growth_bytes"] - after["open_growth_bytes"] > payload_bytes * 0.5
    )
    assert after["access_growth_bytes"] > payload_bytes * 0.75


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("warmup", type=Path)
    parser.add_argument("--backend-source", type=Path)
    arguments = parser.parse_args()
    print(
        json.dumps(_measure(arguments.path, arguments.warmup, arguments.backend_source))
    )
