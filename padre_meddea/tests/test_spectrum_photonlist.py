import numpy as np
import pytest
from astropy.timeseries import TimeSeries
from specutils import Spectrum1D

from padre_meddea import _test_files_directory
from padre_meddea.io.file_tools import read_file, read_fits_l0l1_photon, read_raw_a0
from padre_meddea.spectrum import spectrum
from padre_meddea.util.pixels import PixelList

# f1 = _test_files_directory / "padreMDA0_240916122901.dat"
f1 = _test_files_directory / "padreMDA0_260704194521_cal.dat"
f2 = _test_files_directory / "padreMDA0_260704194521_flare.dat"
f3 = _test_files_directory / "padreMDA0_260704194521_particles.dat"


@pytest.fixture
def ph_list():
    return read_file(f1)


def test_photonlist_slice(ph_list):
    """Test that we can slice a photonlist"""
    start_time = ph_list.time[0]
    stop_time = ph_list.time[2]
    ph_list_slice = ph_list[start_time:stop_time]
    assert isinstance(ph_list_slice, spectrum.PhotonList)
    assert np.all(ph_list_slice.event_list.time >= start_time)
    assert np.all(ph_list_slice.event_list.time <= stop_time)
    # slice with string
    ph_list_slice_str = ph_list[str(start_time) : str(stop_time)]
    assert isinstance(ph_list_slice_str, spectrum.PhotonList)
    assert np.all(ph_list_slice_str.event_list.time >= start_time)
    assert np.all(ph_list_slice_str.event_list.time <= stop_time)


def test_photonlist_slice_invalid(ph_list):
    """Test that we raise an error when slicing a photonlist with invalid types"""
    with pytest.raises(ValueError):
        ph_list[0]
    with pytest.raises(ValueError):
        ph_list[0:1]
    with pytest.raises(ValueError):
        ph_list["2026-07-04T20:31:00"]


def test_photonlist_text_summary_contains_event_count(ph_list):
    """Test that PhotonList string summary reports the event count."""
    text_summary = ph_list._text_summary()
    assert (
        "PhotonList (2,450 events)\n2026-07-04 20:08:17.198 - 20:09:57.190 (1min 39.992s)\n"
        in text_summary
    )


def test_photonlist_add(ph_list):
    """Test that we can add two photonlists together"""
    ph_list1 = ph_list[ph_list.time[2] : ph_list.time[3]]
    ph_list2 = ph_list[ph_list.time[0] : ph_list.time[1]]

    ph_list3 = ph_list1 + ph_list2
    assert isinstance(ph_list3, spectrum.PhotonList)
    assert len(ph_list3.event_list) == len(ph_list1.event_list) + len(
        ph_list2.event_list
    )


@pytest.mark.parametrize(
    "file",
    [f1, f2, f3] + list((_test_files_directory / "photon").glob("*.fits")),
)
def test_photonlist(file):
    """Test that we can create a spectrumlist from a raw file"""
    if file.suffix == ".dat":
        phlist = read_raw_a0(file)
        assert phlist.meta is None
    else:
        phlist = read_fits_l0l1_photon(file)
        assert phlist.meta is not None
        assert isinstance(phlist.meta, dict)
        assert "AUTHOR" in phlist.meta
        assert phlist.meta["AUTHOR"] == "Steven D. Christe"

    assert isinstance(phlist, spectrum.PhotonList)

    assert isinstance(phlist.pixel_list, PixelList)
    assert isinstance(phlist.event_list, TimeSeries)
    assert isinstance(phlist.pkt_list, TimeSeries)

    assert len(phlist.event_list) > 0
    assert len(phlist.pkt_list) > 0
    assert phlist.data  # just check that it exists
    assert np.all(phlist.data["event_list"] == phlist.event_list)
    assert np.all(phlist.data["pkt_list"] == phlist.pkt_list)
    assert phlist.calibrated is False
    assert isinstance(phlist.spectrum(pixel_list=phlist.pixel_list), Spectrum1D)
    assert isinstance(phlist.spectrum(), Spectrum1D)


def test_calibrate(ph_list):
    """Test that we can calibrate a photonlist"""
    ph_list.calibrate()
    assert ph_list.calibrated is True
    assert "energy" in ph_list.event_list.colnames
    assert isinstance(ph_list.spectrum(pixel_list=ph_list.pixel_list), Spectrum1D)


def test_calibrate_nobaseline(ph_list):
    """Test that we raise an error when calibrating a photonlist without baseline column"""
    # remove the baseline column
    ph_list.event_list.remove_column("baseline")
    with pytest.raises(ValueError):
        ph_list.calibrate()
