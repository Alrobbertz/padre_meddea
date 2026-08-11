.. _energy_calibration:

******************
Energy Calibration
******************

This guide provides an overview of the energy calibration process for photon data.
Energy calibration is a crucial step in analyzing photon data, as it ensures that the measured energies of events are accurate and enables data from all detectors to be combined into a single spectrum.

.. doctest::

   >>> from padre_meddea.data.sample import PHOTON_L0_FILE as sample_file  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   INFO: ...
   >>> from padre_meddea.io import read_file
   >>> ph_list = read_file(sample_file)
   >>> print(ph_list._text_summary())
   PhotonList (1,273,965 events)
   2026-07-04 19:45:14.869 - 20:47:23.344 (1hr 2min 8.476s)

This sample file includes a solar flare event as well as calibration data, which is useful to confirm the energy calibration process.
The event data is contained in the `event_list` attribute of the `PhotonList` object, which is a structured array with fields for time, sequence count, clocks, ASIC, channel, A-to-D conversion value, baseline, packet times, packet clock, and pixel number.

.. doctest::

   >>> ph_list.event_list[0]
   <Row index=0>
            time          seqcount clocks  asic channel  atod  baseline  pkttimes pktclock pixel
            Time           uint16  uint16 uint8  uint8  uint16  uint16    uint32   uint32  int64
   ----------------------- -------- ------ ----- ------- ------ -------- --------- -------- -----
   2026-07-04 19:45:14.869     3511      0     0       0   1257     3583 836509519 17371652     7

In order to calibrate the energy of the photon data, the `calibrate()` method of the `PhotonList` object can be used. This method applies the necessary calibration factors to the A-to-D conversion values, resulting in calibrated energy values for each event.
This function applies a unique calibration profile to each detector and each pixel.
It adds a new column to the `event_list` structured array called `energy`, which contains the calibrated energy values in keV.

.. doctest::

   >>> ph_list.calibrate()
   >>> print(ph_list.event_list['energy'][0])
   33.84298173135698

Now that the energy calibration has been applied, the `energy` field can be used for further analysis, such as generating energy spectra.
First it is usually a good idea to have a look at the spectrogram.

.. plot::

   >>> import matplotlib.pyplot as plt
   >>> from padre_meddea.data.sample import PHOTON_L0_FILE as sample_file  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   INFO: ...
   >>> from padre_meddea.io import read_file
   >>> ph_list = read_file(sample_file)
   >>> ph_list.calibrate()
   >>> ph_list.plot_spectrogram() # doctest: +SKIP


The spectrogram shows the flare starts at around 2026-07-04T20:35:00.
The data between 20:08 and 20:30 show the Ba-133 calibration source, which is used to calibrate the energy of the photon data.
Let's plot the spectrum for that time period.

.. plot::

   >>> import matplotlib.pyplot as plt
   >>> from padre_meddea.data.sample import PHOTON_L0_FILE as sample_file # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   INFO: ...
   >>> from padre_meddea.io import read_file
   >>> ph_list = read_file(sample_file)
   >>> ph_list.calibrate()
   >>> ph_list['2026-07-04T20:08:00':'2026-07-04T20:30:00'].spectrum().plot() # doctest: +SKIP

Finally, let's plot the spectrum for the flare event.

.. plot::

   >>> import matplotlib.pyplot as plt
   >>> from padre_meddea.data.sample import PHOTON_L0_FILE as sample_file  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   INFO: ...
   >>> from padre_meddea.io import read_file
   >>> ph_list = read_file(sample_file)
   >>> ph_list.calibrate()
   >>> ph_list['2026-07-04T20:35:00':'2026-07-04T20:45:00'].spectrum().plot() # doctest: +SKIP

You can also plot the light curve for a specific energy range.

.. plot::

   >>> import matplotlib.pyplot as plt
   >>> import astropy.units as u
   >>> from padre_meddea.data.sample import PHOTON_L0_FILE as sample_file  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   INFO: ...
   >>> from padre_meddea.io import read_file
   >>> ph_list = read_file(sample_file)
   >>> ph_list.calibrate()
   >>> ts = ph_list.lightcurve(energy_edges=(5, 30, 50) * u.keV, time_bin_size=1 * u.s)
   >>> plt.plot(ts.time.datetime, ts["5to30_keV"]) # doctest: +SKIP
   >>> plt.plot(ts.time.datetime, ts["30to50_keV"]) # doctest: +SKIP
