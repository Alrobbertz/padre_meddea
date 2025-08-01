"""
This module provides tools to analyze and manipulate meddea spectral data both summary spectra and event lists.
"""

import numpy as np

import astropy.units as u
from astropy.time import Time
from astropy.nddata import StdDevUncertainty
from astropy.table import Table
from astropy.timeseries import TimeSeries, BinnedTimeSeries, aggregate_downsample

from specutils import Spectrum1D, SpectralRegion

import padre_meddea.util.util as util
from padre_meddea.util.pixels import PixelList

DEFAULT_SPEC_PIXEL_IDS = np.array(
    [
        51738,
        51720,
        51730,
        51712,
        51733,
        51715,
        51770,
        51752,
        51762,
        51744,
        51765,
        51747,
        51802,
        51784,
        51794,
        51776,
        51797,
        51779,
        51834,
        51816,
        51826,
        51808,
        51829,
        51811,
    ],
    dtype=np.uint16,
)
MAX_PH_DATA_RATE = 100 * u.kilobyte / u.s

DEFAULT_SPEC_PIXEL_LIST = PixelList(pixelids=DEFAULT_SPEC_PIXEL_IDS)

__all__ = [
    "PhotonList",
    "SpectrumList",
]


class PhotonList:
    """Data container for MeDDEA photon or event list data

    Parameters
    ----------
    pkt_list : TimeSeries
        The time series of photon packet header data.
    event_list : TimeSeries
        The time series of event data
    """

    def __init__(self, pkt_list: TimeSeries, event_list: TimeSeries):
        self.data = {"event_list": event_list, "pkt_list": pkt_list}
        self.event_list = event_list
        self.pkt_list = pkt_list

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.event_list[key]
        elif isinstance(key, slice):
            if isinstance(key.start, Time) and isinstance(key.stop, Time):
                pkt_ind = (self.pkt_list.time > key.start) * (
                    self.pkt_list.time < key.stop
                )
                ph_ind = (self.event_list.time > key.start) * (
                    self.event_list.time < key.stop
                )
                return type(self)(self.pkt_list[pkt_ind], self.event_list[ph_ind])
        return self

    def __str__(self):
        return f"{self._text_summary()}{self.data.__repr__()}"

    def __repr__(self):
        return f"{object.__repr__(self)}\n{self}"

    def _text_summary(self):
        dt = self.data["event_list"].time[-1] - self.data["event_list"].time[0]
        dt.format = "quantity_str"
        result = f"PhotonList ({len(self.data['event_list']):,} events)\n"
        if dt < (1 * u.day):
            result += f"{self.data['event_list'].time[0]} - {str(self.data['event_list'].time[-1])[11:]} ({dt})\n"
        else:
            result += f"{self.data['event_list'].time[0]} - {self.data['event_list'].time[-1]} ({dt})\n"
        return result

    @property
    def calibrated(self):
        if "energy" in self.event_list.colnames:
            return True
        else:
            return False

    @property
    def pixel_list(self) -> PixelList:
        """Return the set of pixels that have events"""
        # note this is calculated on the fly instead of at init because it can take a few seconds to compute for large event lists
        pixel_ids = np.unique(
            util.get_pixelid(self.event_list["asic"], self.event_list["pixel"])
        )
        return PixelList(pixelids=pixel_ids)

    def spectrum(
        self,
        pixel_list: PixelList,
        bins=None,
        baseline_sub: bool = False,
        calibrate: bool = False,
    ) -> Spectrum1D:
        """
        Create a spectrum

        Parameters
        ----------
        pixel_list : PixelList
            A list of one or more pixels
        bins : np.array
            The bin edges for the spectrum (see ~np.histogram).
            If None, then uses np.arange(0, 2**12 - 1)
        baseline_sub : bool
            If True, then baseline measurements are subtracted if they exist
            Note: not yet implemented.
        calibrate : bool
            If True, provide the calibrated spectrum

        Returns
        -------
        spectrum : Spectrum1D
        """
        if not calibrate and bins is None:
            bins = np.arange(0, 2**12 - 1) * u.pix
        if calibrate and bins is None:
            bins = np.arange(0, 100, 0.1) * u.keV
        this_event_list = self._slice_event_list_pixels(pixel_list)
        if calibrate:
            hit_energy = this_event_list["energy"]
        else:
            hit_energy = this_event_list["atod"]
        data, new_bins = np.histogram(hit_energy, bins=bins.value)

        # for Spectrum1D, the spectral axis is at the center of the bins
        # TODO: the histogram results are not consistent with the above
        result = Spectrum1D(
            flux=u.Quantity(data, "count"),
            spectral_axis=bins,
            uncertainty=StdDevUncertainty(np.sqrt(data) * u.count),
        )
        return result

    def lightcurve(
        self,
        pixel_list: PixelList,
        int_time: u.Quantity[u.s],
        sr: SpectralRegion,
        step: int = 10,
    ) -> TimeSeries:
        """
        Create a light curve

        Parameters
        ----------
        pixel_list : PixelList
            The pixels to integrate over
        int_time : u.Quantity[u.s]
            The integration time for each time step
        sr : SpectralRegion
            The spectral region(s) to integrate over
        step : int
            To speed up processing, skip every `step` photons.
            Default is ten.
            The light curve count rate is corrected by multiplying by `step`.

        Returns
        -------
        lc : TimeSeries
        """
        this_event_list = self._slice_event_list_pixels(pixel_list)
        # downsample the event list
        this_event_list = TimeSeries(time=self.event_list.time[::step])
        for this_sr in sr:
            this_event_list = self._slice_event_list_sr(sr)
            col_label = f"{this_sr.lower}-{this_sr.upper}_cts"
            this_event_list[col_label] = np.ones(len(this_event_list))
            ts = aggregate_downsample(
                this_event_list, time_bin_size=int_time, aggregate_func=np.sum
            )
            ts[col_label] *= step
        return ts

    def data_rate(self) -> BinnedTimeSeries:
        """Return a BinnedTimeseries of the data rate.

        Returns
        -------
        data_rate : BinnedTimeSeries
        """
        # correct the ccsds packet length by adding ccsds header and adding missing 1
        pkt_length = (self.pkt_list["pktlength"] + 3 * 2 + 1) * u.byte
        good_times = (
            self.pkt_list.time > self.pkt_list.time[0]
        )  # to protect against bad times

        data_rate = TimeSeries(
            time=self.pkt_list.time[good_times],
            data={"packet_size": pkt_length[good_times]},
        )
        data_rate_ts = aggregate_downsample(
            data_rate, time_bin_size=1 * u.s, aggregate_func=np.sum
        )
        data_rate_ts.rename_column("packet_size", "data_rate")
        data_rate_ts["data_rate"] = data_rate_ts["data_rate"] / u.s
        return data_rate_ts

    def _slice_event_list_pixels(self, pixel_list: PixelList) -> TimeSeries:
        """Slice the event list to only contain events from asic_num and pixel_num"""
        ind = np.zeros(len(self.event_list), dtype=np.bool)
        if isinstance(pixel_list, Table.Row):
            ind = np.logical_or(
                ind,
                (self.event_list["pixel"] == int(pixel_list["pixel"]))
                * (self.event_list["asic"] == int(pixel_list["asic"])),
            )
        else:
            for this_pixel in pixel_list:
                ind = np.logical_or(
                    ind,
                    (self.event_list["pixel"] == int(this_pixel["pixel"]))
                    * (self.event_list["asic"] == int(this_pixel["asic"])),
                )
        return self.event_list[ind]

    def _slide_event_list_sr(self, sr: SpectralRegion):
        """Slice the envt list to only contain events inside the spectral region."""
        if len(sr) > 1:
            raise ValueError("Only supports Spectral Regions of length 1.")
        if sr[0].lower.unit == u.Unit("keV"):
            data = self.event_list["energy"]
        elif sr[0].lower.unit == u.Unit("pix"):
            data = self.event_list["atod"]
        else:
            raise ValueError(
                f"Unit of Spectral Region, {sr[0].lower.unit}, not recognized."
            )
        ind = (data > sr[0].lower) * (data < sr[0].upper)
        return self.event_list[ind]


class SpectrumList:
    """
    A data container for MeDDEA summary spectrum data

    Parameters
    ----------
    pkt_spec : TimeSeries
        The time series of spectrum packet header data.
    specs : Spectrum1D
        The spectrum cube
    pixel_ids : np.array
        The pixel id array

    Raises
    ------
    ValueError
        If pixel arrays are found to change.

    Examples
    --------
    >>> from padre_meddea.io.file_tools import read_file
    >>> from astropy.time import Time
    >>> spec_list = read_file("padre_meddea_l0test_spectrum_20250504T070411_v0.1.0.fits")  # doctest: +SKIP
    >>> this_spectrum = this_spec_list.spectrum(asic_num=0, pixel_num=0)  # doctest: +SKIP
    """

    def __init__(self, pkt_list: TimeSeries, specs, pixel_ids):
        self.bins = np.arange(0, 4097, 8, dtype=np.uint16)
        self.time = pkt_list.time
        self.data = {"pkt_list": pkt_list, "specs": specs, "pixel_ids": pixel_ids}
        self.pkt_list = self.data["pkt_list"]
        self.specs = self.data["specs"]
        self._pixel_ids = self.data["pixel_ids"]
        if len(np.unique(pixel_ids)) > 24:
            print("Found too many unique pixel IDs.")
            print("Forcing to default set")
            self.pixel_list = PixelList(pixelids=DEFAULT_SPEC_PIXEL_IDS)
        else:
            if np.all(np.unique(pixel_ids) == sorted(pixel_ids[0, :])):
                self.pixel_list = PixelList(
                    pixelids=np.median(pixel_ids, axis=0).astype("uint16")
                )
            else:
                raise ValueError("Found change in pixel ids")
        self.index = len(pkt_list)

    @property
    def calibrated(self):
        if self.specs[0, 0].spectral_axis.unit == u.Unit("keV"):
            return True
        else:
            return False

    def __str__(self):
        return f"{self._text_summary()}{self.data['specs'].__repr__()}"

    def __repr__(self):
        return f"{object.__repr__(self)}\n{self}"

    def _text_summary(self):
        dt = self.time[-1] - self.time[0]
        dt.format = "quantity_str"
        result = f"SpectrumList ({self.specs.shape[0]:,} spectra, {int(np.sum(self.specs.data)):,} events)\n"
        if dt < (1 * u.day):
            result += f"{self.time[0]} - {str(self.time[-1])[11:]} ({dt})\n"
        else:
            result += f"{self.time[0]} - {self.time[-1]} ({dt})\n"
        return result

    def spectrum(self, pixel_list: PixelList):
        """Create a spectrum, integrates over all times

        Parameters
        ----------
        asic_num : int
            The asic or detector number (0 to 3)
        pixel_num : int
            The pixel number (0 to 11)
        or
        spec_index : int
            The spectrum index from 0 to 23

        Raises
        ------
        ValueError
            If the selected asic_num and pixel_num are not found in the spectra

        Returns
        -------
        spectrum : Spectrum1D
        """
        flux = np.zeros([self.specs.data.shape[2]])
        if isinstance(pixel_list, Table.Row):
            if pixel_list in self.pixel_list:
                pixel_index = np.where(pixel_list == self.pixel_list)[0][0]
                flux += np.sum(self.specs.data[:, pixel_index, :], axis=0)
        else:
            for this_pixel in pixel_list:
                if this_pixel in self.pixel_list:
                    pixel_index = np.where(this_pixel == self.pixel_list)[0][0]
                    flux += np.sum(self.specs.data[:, pixel_index, :], axis=0)
        # the spectral axis is at the center of the bins
        result = Spectrum1D(
            flux=flux * self.specs[0, 0].flux.unit,
            spectral_axis=self.specs[0, 0].spectral_axis,
            uncertainty=StdDevUncertainty(np.sqrt(flux) * u.count),
        )
        return result

    def lightcurve(self, pixel_list: PixelList, sr: SpectralRegion) -> TimeSeries:
        """
        Create a light curve

        Parameters
        ----------
        pixel_index : int
            The pixels to integrate over
        sr : SpectralRegion
            The spectral region(s) to integrate over

        Returns
        -------
        lc : TimeSeries
        """
        lc = TimeSeries(time=self.time)
        flux = np.zeros([self.specs.data.shape[0], self.specs.data.shape[2]])
        if isinstance(pixel_list, Table.Row):
            if pixel_list in self.pixel_list:
                pixel_index = np.where(pixel_list == self.pixel_list)[0][0]
                flux += self.specs.data[:, pixel_index, :]
        else:
            for this_pixel in pixel_list:
                if this_pixel in self.pixel_list:
                    pixel_index = np.where(this_pixel == self.pixel_list)[0][0]
                    flux += self.specs.data[:, pixel_index, :]
        for i, this_sr in enumerate(sr):
            this_flux = flux.copy()
            ind = (self.specs[0, 0].spectral_axis > this_sr.lower) * (
                self.specs[0, 0].spectral_axis < this_sr.upper
            )
            this_flux[:, ~ind] = 0
            col_label = f"{this_sr.lower}-{this_sr.upper}_cts"
            total_cts = np.sum(this_flux, axis=1)
            lc[col_label] = total_cts
        return lc

    def plot_spectrogram(self, **imshow_kwargs):
        """Plot a spectrogram"""
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        ts = [mdates.date2num(this_time) for this_time in self.time.to_datetime()]
        x_lims = [ts[0], ts[-1]]
        y_lims = [
            self.specs[0, 0].spectral_axis[0].value,
            self.specs[0, 0].spectral_axis[-1].value,
        ]
        fig, ax = plt.subplots()
        specgram = np.sum(self.specs.data, axis=1)
        ax.imshow(
            specgram.transpose(),
            origin="lower",
            interpolation="nearest",
            extent=[x_lims[0], x_lims[1], y_lims[0], y_lims[1]],
            **imshow_kwargs,
        )
        date_format = mdates.DateFormatter("%H:%M:%S")
        ax.xaxis.set_major_formatter(date_format)
        # This simply sets the x-axis data to diagonal so it fits better.
        fig.autofmt_xdate()
        plt.show()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.specs[key]
        elif isinstance(key, slice):
            if isinstance(key.start, Time) and isinstance(key.stop, Time):
                ind = (self.time > key.start) * (self.time < key.stop)
                return type(self)(
                    self.pkt_list[ind], self.specs[ind, :, :], self._pixel_ids
                )
        return self
