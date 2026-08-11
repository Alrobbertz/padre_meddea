from pathlib import Path

import pytest

import padre_meddea
import padre_meddea.data._sample as _sample
import padre_meddea.data.sample as sample


@pytest.fixture(autouse=True)
def _no_real_downloads(monkeypatch):
    """Ensure no test in this module can hit the network."""

    def mock_urlretrieve(url, filename):
        Path(filename).write_bytes(b"test")
        return filename, None

    monkeypatch.setattr(_sample, "urlretrieve", mock_urlretrieve)


def test_get_sampledata_dir_defaults_to_home(monkeypatch):
    """Falls back to ~/.padre_meddea/data when no download_dir override is configured."""
    monkeypatch.setattr(padre_meddea, "config", {})

    result = _sample._get_sampledata_dir()

    assert result == Path.home() / ".padre_meddea" / "data"


def test_get_sampledata_dir_honors_config_override(monkeypatch, tmp_path):
    """Uses padre_meddea.config['downloads']['download_dir'] when set."""
    override_dir = tmp_path / "configured-downloads"
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(override_dir)}}
    )

    result = _sample._get_sampledata_dir()

    assert result == override_dir
    assert result.exists()


def test_get_sampledata_dir_relative_override_resolved_against_package_dir(
    monkeypatch, tmp_path
):
    """Relative download_dir overrides are resolved against _package_directory."""
    monkeypatch.setattr(padre_meddea, "_package_directory", tmp_path)
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": "relative/data"}}
    )

    result = _sample._get_sampledata_dir()

    assert result == tmp_path / "relative/data"


def test_get_sample_files_downloads_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )
    url = "https://example.com/some_file.fits"

    result = _sample._get_sample_files([url])

    assert result == [tmp_path / "some_file.fits"]
    assert result[0].exists()


def test_get_sample_files_skips_existing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )
    url = "https://example.com/some_file.fits"
    existing = tmp_path / "some_file.fits"
    existing.write_bytes(b"already here")

    calls = []
    monkeypatch.setattr(
        _sample,
        "urlretrieve",
        lambda url, filename: calls.append(filename),
    )

    result = _sample._get_sample_files([url])

    assert result == [existing]
    assert calls == []
    assert existing.read_bytes() == b"already here"


def test_get_sample_files_force_download_overwrites(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )
    url = "https://example.com/some_file.fits"
    existing = tmp_path / "some_file.fits"
    existing.write_bytes(b"stale")

    result = _sample._get_sample_files([url], force_download=True)

    assert result == [existing]
    assert existing.read_bytes() == b"test"


def test_get_sample_files_no_download_returns_none_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )
    url = "https://example.com/some_file.fits"

    result = _sample._get_sample_files([url], no_download=True)

    assert result == [None]


def test_sample_getattr_returns_cached_path(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )

    result = sample.PHOTON_L0_FILE

    expected_name = Path(_sample._SAMPLE_DATA["PHOTON_L0_FILE"]).name
    assert result == tmp_path / expected_name
    assert result.exists()


def test_sample_getattr_unknown_attribute_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )

    with pytest.raises(AttributeError):
        sample.NOT_A_REAL_SAMPLE_FILE


def test_sample_file_dict_and_file_list(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )

    # Nothing downloaded yet -> file_dict values are None, file_list is empty.
    assert sample.file_dict == {"PHOTON_L0_FILE": None}
    assert sample.file_list == []

    # Trigger the download, then file_dict/file_list should reflect the cached file.
    downloaded = sample.PHOTON_L0_FILE
    assert sample.file_dict == {"PHOTON_L0_FILE": downloaded}
    assert sample.file_list == [downloaded]


def test_download_all(monkeypatch, tmp_path):
    monkeypatch.setattr(
        padre_meddea, "config", {"downloads": {"download_dir": str(tmp_path)}}
    )

    sample.download_all()

    expected_name = Path(_sample._SAMPLE_DATA["PHOTON_L0_FILE"]).name
    assert (tmp_path / expected_name).exists()
