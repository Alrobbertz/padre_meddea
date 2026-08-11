"""
Private implementation details for the sample data downloader.

See :mod:`padre_meddea.data.sample` for the public, user-facing API.
"""

from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

import padre_meddea
from padre_meddea import log

# Shortcut requirements:
# - key: an importable, all-caps name exposed from `padre_meddea.data.sample`
# - value: the full download URL for that file (PADRE sample files live under
#   per-descriptor/date subpaths, so unlike sunpy there is no single shared
#   base URL to combine with a bare filename)
_SAMPLE_DATA = {
    "PHOTON_L0_FILE": (
        "https://umbra.nascom.nasa.gov/padre/padre-meddea/l0/photon/2026/07/04/"
        "padre_meddea_l0_photon_20260704T194514_v1.0.0.fits"
    ),
}


def _get_sampledata_dir() -> Path:
    """
    Return the directory where sample data files are cached, creating it if needed.

    The directory can be overridden by setting ``download_dir`` under the
    ``downloads`` key of ``padre_meddea.config``. Relative paths are resolved
    against the package directory. If no override is configured, defaults to
    ``~/.padre_meddea/data``.
    """
    download_dir = padre_meddea.config.get("downloads", {}).get("download_dir")
    if download_dir:
        base_dir = Path(download_dir)
        if not base_dir.is_absolute():
            base_dir = padre_meddea._package_directory / base_dir
    else:
        base_dir = Path.home() / ".padre_meddea" / "data"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _get_sample_files(
    urls, no_download: bool = False, force_download: bool = False
) -> list[Optional[Path]]:
    """
    Return local paths for a list of sample data URLs, downloading as needed.

    Parameters
    ----------
    urls : list of str
        Full download URLs for the requested sample files.
    no_download : bool
        If `True`, never download; return `None` for any file not already cached.
    force_download : bool
        If `True`, re-download every file even if it is already cached.

    Returns
    -------
    list of `pathlib.Path` or `None`
        Local cached path for each requested URL, in order.
    """
    sampledata_dir = _get_sampledata_dir()
    fullpaths = [sampledata_dir / Path(url).name for url in urls]

    if no_download:
        return [fp if fp.exists() else None for fp in fullpaths]

    for url, fullpath in zip(urls, fullpaths):
        if force_download or not fullpath.exists():
            log.info(f"Downloading sample data file from {url} to {fullpath}")
            urlretrieve(url, str(fullpath))
        else:
            log.info(
                f"Sample data file already exists at {fullpath}, using local files."
            )

    return fullpaths
