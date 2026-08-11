"""
Sample data files for use with PADRE MeDDEA.

This module provides sample data files that are downloaded on first access
and then cached locally. When a sample shortname is accessed as an attribute
of this module, the corresponding file is downloaded (if not already cached)
and its local path is returned. All files can be downloaded ahead of time by
calling :func:`~padre_meddea.data.sample.download_all`.

Available sample shortnames:

- ``PHOTON_L0_FILE``: an example Level 0 photon FITS file containing a solar
  flare event and Ba-133 calibration source data.
"""

from ._sample import _SAMPLE_DATA, _get_sample_files

# file_dict and file_list are not normal variables; see __getattr__() below
__all__ = list(sorted(_SAMPLE_DATA.keys())) + [
    "download_all",
    "file_dict",  # noqa: F822
    "file_list",  # noqa: F822
]


def __dir__():
    return __all__


def __getattr__(name):
    if name in _SAMPLE_DATA:
        return _get_sample_files([_SAMPLE_DATA[name]])[0]
    elif name == "file_dict":
        return dict(
            sorted(
                zip(
                    _SAMPLE_DATA.keys(),
                    _get_sample_files(_SAMPLE_DATA.values(), no_download=True),
                )
            )
        )
    elif name == "file_list":
        return [v for v in __getattr__("file_dict").values() if v]
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def download_all(force_download=False):
    """
    Download all sample data at once that has not already been downloaded.

    Parameters
    ----------
    force_download : `bool`
        If `True`, files are downloaded even if they already exist. Default is
        `False`.
    """
    _get_sample_files(_SAMPLE_DATA.values(), force_download=force_download)
