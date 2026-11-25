# /// script
# requires-python = ">=3.11"
# dependencies = ["sdf-xarray>=0.10.1", "sdfr>=1.4.13", "matplotlib", "memray"]
# ///
"""Benchmark the time and memory needed by sdf-xarray and sdf_helper (which is
distributed in the sdfr package) to:

1. Open a single SDF file, for files of increasing size
2. Take a lineout through a time series, for an increasing number of files

EPOCH is run to create the SDF files, then each measurement is made in a fresh
Python process.

Run with ``uv run benchmark.py path/to/epoch/epoch2d/bin/epoch2d`` (Linux or
macOS, as memray does not support Windows).
"""

import multiprocessing
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from sys import argv

import epydeck
import matplotlib.pyplot as plt
import memray
import numpy as np
from sdfr import sdf_helper

import sdf_xarray as sdfxr

EPOCH_2D = Path(argv[1])
BENCHMARK_PATH = Path(__file__).parent
DATA_DIR = Path(BENCHMARK_PATH / "benchmark_data")
GRID_SIZES = [128, 256, 512, 1024, 2048, 4096, 8192]
NUM_FILES = [1, 2, 4, 8, 16, 32, 64]

# An empty box that writes the electric and magnetic fields every femtosecond
# until t_end. Only the size and number of SDF files matter for this benchmark.
deck = {
    "control": {
        "t_end": 0,
        "x_min": 0,
        "x_max": 50e-6,
        "y_min": -25e-6,
        "y_max": 25e-6,
    },
    "boundaries": {
        "bc_x_min": "open",
        "bc_x_max": "open",
        "bc_y_min": "open",
        "bc_y_max": "open",
    },
    "output": {
        "dt_snapshot": "1 * femto",
        "dump_last": False,
        "ex": "always",
        "ey": "always",
        "ez": "always",
        "bx": "always",
        "by": "always",
        "bz": "always",
    },
}


def run_epoch(name, n, t_end=0):
    """Run EPOCH on an n x n grid until t_end and return the SDF files it writes"""
    folder = DATA_DIR / name
    if not any(folder.glob("*.sdf")):
        folder.mkdir(parents=True, exist_ok=True)

        deck["control"]["nx"] = n
        deck["control"]["ny"] = n
        deck["control"]["t_end"] = t_end
        with (folder / "input.deck").open("w") as f:
            epydeck.dump(deck, f)

        subprocess.run(
            [EPOCH_2D],
            input=str(folder),
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,  # Ignore simulation output
        )
    return sorted(folder.glob("*.sdf"))


def open_file_with_reader(library, path):
    if library == "sdf-xarray":
        return sdfxr.open_dataset(path)
    return sdf_helper.getdata(str(path), verbose=False)


def lineout_over_time(library, paths):
    """Ey along x through the middle of y, from every file, as a (time, x) array"""
    if library == "sdf-xarray":
        ey = sdfxr.open_mfdataset(paths)["Electric_Field_Ey"]
        return ey.isel(Y_Grid_mid=ey.sizes["Y_Grid_mid"] // 2).values

    lineouts = []
    for path in paths:
        ey = sdf_helper.getdata(str(path), verbose=False).Electric_Field_Ey.data
        # Copy so that only the lineout is kept, not all of ey
        lineouts.append(ey[:, ey.shape[1] // 2].copy())
    return np.array(lineouts)


# NOTE Both libraries do some one-off setup the first time they are used
# (e.g. xarray imports dask), so the measurements below run each task on a
# different small file first


def measure_time(task, library, files, warm_up):
    """Time taken (ms) to run task on files"""
    task(library, warm_up)
    start = time.perf_counter()
    task(library, files)
    return (time.perf_counter() - start) * 1e3


def measure_memory(task, library, files, warm_up):
    """Peak memory (MB) allocated while running task on files, measured with memray"""
    task(library, warm_up)
    memray_file = DATA_DIR / f"{library}.memray"
    memray_file.unlink(missing_ok=True)

    with memray.Tracker(memray_file):
        task(library, files)
    return memray.FileReader(memray_file).metadata.peak_memory / 1e6


def run_in_new_process(function, *args):
    # A new process every time, so nothing is cached from previous runs
    spawn = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=spawn) as pool:
        return pool.submit(function, *args).result()


def run_benchmark(task, inputs, warm_up, x, x_label):
    """Time (ms) and peak memory (MB) for each library to run task on each input"""
    results = {}
    for library in ["sdf-xarray", "sdf_helper"]:
        times, memory = [], []
        for files, x_value in zip(inputs, x):
            # CPU runtime is non-deterministic and therefore should be
            # calculated using an average of several measurements
            runs = [
                run_in_new_process(measure_time, task, library, files, warm_up)
                for _ in range(10)
            ]
            times.append(statistics.median(runs))
            memory.append(
                # Memory is only calculated once as it is deterministic
                run_in_new_process(measure_memory, task, library, files, warm_up)
            )
            print(
                f"{library:>10} | {x_label}: {x_value:7.1f} | "
                f"{times[-1]:8.2f} ms | {memory[-1]:7.1f} MB memory"
            )
        results[library] = times, memory
    return results


def plot(results, x, x_label, filename):
    fig, (ax_memory, ax_time) = plt.subplots(1, 2, figsize=(11, 4.5))

    styles = {
        "sdf-xarray": ("#2a78d6", "o", "sdf-xarray (v0.10.1)"),
        "sdf_helper": ("#eb6834", "s", "sdf_helper (v1.4.13)"),
    }
    for library, (times, memory) in results.items():
        colour, marker, label = styles[library]
        line_style = {"color": colour, "marker": marker, "lw": 2, "ms": 8}
        ax_memory.plot(x, memory, label=label, **line_style)
        ax_time.plot(x, times, label=label, **line_style)

    ax_memory.set(ylabel="Peak memory allocated (MB)")
    ax_time.set(ylabel="Wall-clock time (ms)")
    for ax in (ax_memory, ax_time):
        ax.set(xscale="log", yscale="log", xlabel=x_label)
        ax.grid(color="0.9")
    ax_memory.legend()

    plt.tight_layout()
    fig.savefig(BENCHMARK_PATH / filename, dpi=500)


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 13})
    warm_up_file = run_epoch("64x64", 64)[0]

    # 1. Open single files of increasing size
    sdf_files = [run_epoch(f"{n}x{n}", n)[0] for n in GRID_SIZES]
    file_sizes = [path.stat().st_size / 1e6 for path in sdf_files]
    x_label = "SDF file size (MB)"
    results = run_benchmark(
        open_file_with_reader, sdf_files, warm_up_file, file_sizes, x_label
    )
    plot(results, file_sizes, x_label, "benchmark.png")

    # 2. Take a lineout through a time series of an increasing number of files
    time_series = run_epoch("time_series", 1024, t_end="64 * femto")
    inputs = [time_series[:n] for n in NUM_FILES]
    x_label = "Number of SDF files"
    results = run_benchmark(
        lineout_over_time, inputs, [warm_up_file], NUM_FILES, x_label
    )
    plot(results, NUM_FILES, x_label, "benchmark_time_series.png")
