import astropy.units as u
import numpy as np
import pytest
from astropy.time import Time
from astropy.timeseries import TimeSeries
from specutils import SpectralRegion, Spectrum1D

from padre_meddea import _test_files_directory
from padre_meddea.io.file_tools import read_fits_l0l1_spectrum, read_raw_a2
from padre_meddea.spectrum import spectrum
from padre_meddea.util.pixels import PixelList

f1 = _test_files_directory / "padreMDA0_240916122901.dat"
f2 = _test_files_directory / "padreMDA2_240916122851.dat"
f3 = _test_files_directory / "padreMDU8_240916122904.dat"


@pytest.mark.parametrize(
    "file",
    [_test_files_directory / "padreMDA2_240916122851.dat"]
    + list((_test_files_directory / "spec").glob("*.fits")),
)
def test_spectrumlist(file):
    """Test that we can create a spectrumlist from a raw file"""
    if file.suffix == ".dat":
        speclist = read_raw_a2(file)
    else:
        speclist = read_fits_l0l1_spectrum(file)
    assert isinstance(speclist, spectrum.SpectrumList)

    assert isinstance(speclist.pixel_list, PixelList)
    assert speclist.data
    assert isinstance(speclist.pkt_list, TimeSeries)
    assert isinstance(speclist.specs, Spectrum1D)
    assert isinstance(speclist.time, Time)
    assert speclist.calibrated is False
    assert isinstance(speclist.spectrum(pixel_list=speclist.pixel_list), Spectrum1D)
    assert isinstance(
        speclist.lightcurve(
            pixel_list=speclist.pixel_list,
            sr=SpectralRegion([[500, 1000]] * u.pix),
        ),
        TimeSeries,
    )
    assert np.all(speclist.data["pkt_list"] == speclist.pkt_list)
    assert np.all(speclist.data["specs"] == speclist.specs)
    # perform basic test on the string representation
    str_list = ["SpectrumList", "spectra", "events", "Spectrum1D"]
    repr_str = str(speclist)
    for this_str in str_list:
        assert repr_str.count(this_str) >= 1
