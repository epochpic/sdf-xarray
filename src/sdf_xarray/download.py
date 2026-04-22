from pathlib import Path
from shutil import move
from typing import Literal, TypeAlias

DatasetName: TypeAlias = Literal[
    "test_array_no_grids",
    "test_dist_fn",
    "test_files_1D",
    "test_files_2D_moving_window",
    "test_files_3D",
    "test_mismatched_files",
    "test_two_probes_2D",
    "tutorial_dataset_1d",
    "tutorial_dataset_2d",
    "tutorial_dataset_2d_moving_window",
    "tutorial_dataset_3d",
    "1_1_drifting_bunch",
    "2_1_two_stream_instability",
    "3_3_Gaussian_1d_laser",
    "3_5_Gaussian_beam",
    "4_2_self_heating",
    "4_3_basic_target",
    "4_4_momentum_distribution",
    "5_1_probe",
    "5_2_subsets",
]


def fetch_dataset(
    dataset_name: DatasetName, save_path: Path | str | None = None
) -> Path:
    """
    Downloads the specified dataset from its Zenodo URL. If it is already
    downloaded, then the path to the cached, unzipped directory is returned.

    Parameters
    ---------
    dataset_name
        The name of the dataset to download
    save_path
        The directory to save the dataset to (defaults to the cache folder ``"sdf_datasets"``.
        See `pooch.os_cache` for details on how the cache works)

    Returns
    -------
    Path
        The path to the directory containing the unzipped dataset files

    Examples
    --------
    >>> # Assuming the dataset has not been downloaded yet
    >>> path = fetch_dataset("tutorial_dataset_1d")
    Downloading file 'tutorial_dataset_1d.zip' ...
    Unzipping contents of '.../sdf_datasets/tutorial_dataset_1d.zip' to '.../sdf_datasets/tutorial_dataset_1d'
    >>> path
    '.../sdf_datasets/tutorial_dataset_1d'
    """
    import pooch  # noqa: PLC0415

    logger = pooch.get_logger()
    datasets = pooch.create(
        path=pooch.os_cache("sdf_datasets"),
        base_url="doi:10.5281/zenodo.17618509",
        registry=None,
        retry_if_failed=10,
    )
    datasets.load_registry_from_doi()

    datasets.fetch(
        f"{dataset_name}.zip", processor=pooch.Unzip(extract_dir="."), progressbar=True
    )
    cache_path = Path(datasets.path) / dataset_name

    if save_path is not None:
        save_path = Path(save_path)
        logger.info(
            "Moving contents of '%s' to '%s'",
            cache_path,
            save_path / dataset_name,
        )
        return move(cache_path, save_path / dataset_name)

    return cache_path
