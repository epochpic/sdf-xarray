from pathlib import Path
from shutil import move
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
    import pooch  # noqa: F401

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
        base_url="https://zenodo.org/records/17991042/files",
        registry={
            "test_array_no_grids.zip": "md5:583c85ed8c31d0e34e7766b6d9f2d6da",
            "test_dist_fn.zip": "md5:a582ff5e8c59bad62fe4897f65fc7a11",
            "test_files_1D.zip": "md5:42e53b229556c174c538c5481c4d596a",
            "test_files_2D_moving_window.zip": "md5:3744483bbf416936ad6df8847c54dad1",
            "test_files_3D.zip": "md5:a679e71281bab1d373dc4980e6da1a7c",
            "test_mismatched_files.zip": "md5:710fdc94666edf7777523e8fc9dd1bd4",
            "test_two_probes_2D.zip": "md5:0f2a4fefe84a15292d066b3320d4d533",
            "tutorial_dataset_1d.zip": "md5:7fad744d8b8b2b84bba5c0e705fdef7b",
            "tutorial_dataset_2d.zip": "md5:b7f35c05703a48eb5128049cdd106ffa",
            "tutorial_dataset_2d_moving_window.zip": "md5:a795f40d18df69263842055de4559501",
            "tutorial_dataset_3d.zip": "md5:d9254648867016292440fdb028f717f7",
        },
        retry_if_failed=10,
    )

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
