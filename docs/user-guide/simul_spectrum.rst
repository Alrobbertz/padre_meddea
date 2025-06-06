.. _spectrum,:

**************
Spectrum Tools
**************

Overview
========
This section tools to simulate and analyze spectra.


Simulated Data
--------------
This package provides tools to simulate the data that is expected during science
operations.

.. plot::

    A plot of the sample X class flare time series (SOL2002-07-23):

    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import astropy.units as u
    >>> import padre_meddea.calibration.simul_spec
    >>> from padre_meddea.calibration.simul_spec import get_flare_rate, flare_timeseries
    >>> time = np.arange(10000) * u.s
    >>> cts = get_flare_rate()(time)
    >>> data_limiter = flare_timeseries['sec_from_start'] < time.max()
    >>> y = flare_timeseries['xrsb'][data_limiter] / flare_timeseries['xrsb'].max() * 22421.0
    >>> total_counts = cts.sum() * 4
    >>> plt.plot(flare_timeseries['sec_from_start'][data_limiter], y, label='data [GOES xrbs]')  # doctest: +SKIP
    >>> plt.plot(time, cts, label='Interpolated', alpha=0.5, linewidth=3.0)  # doctest: +SKIP
    >>> plt.legend()  # doctest: +SKIP
    >>> plt.ylabel('cts/s/detector')  # doctest: +SKIP
    >>> plt.xlabel('seconds from start')  # doctest: +SKIP
    >>> plt.title(f'SOL2002-07-23 {total_counts/1e6:.2f} Mcounts')  # doctest: +SKIP

.. plot::

    A plot of the spectrum of our sample X class flare (SOL2002-07-23):

    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import astropy.units as u
    >>> import padre_meddea.calibration.simul_spec
    >>> from padre_meddea.calibration.simul_spec import flare_spectrum, flare_spectrum_data
    >>> energy = np.arange(5, 100, 1) * u.keV
    >>> flux = flare_spectrum(1)(energy)
    >>> data_limiter = flare_spectrum_data['Bin mean (keV)'] < energy.max()
    >>> y = flare_spectrum_data[flare_spectrum_data.colnames[3]][data_limiter]
    >>> plt.plot(flare_spectrum_data['Bin mean (keV)'][data_limiter], y, label='data [RHESSI]')  # doctest: +SKIP
    >>> plt.plot(energy, flux, label='Interpolated', alpha=0.5, linewidth=3.0)  # doctest: +SKIP
    >>> plt.legend()  # doctest: +SKIP
    >>> plt.yscale('log')
    >>> plt.xscale('log')
    >>> plt.ylabel('photon/s/cm ** 2/keV')  # doctest: +SKIP
    >>> plt.xlabel('energy [keV]')  # doctest: +SKIP
    >>> plt.title('SOL2002-07-23')  # doctest: +SKIP

.. plot::

    A plot of our Ba-133 calibration source:

    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import astropy.units as u
    >>> import padre_meddea.calibration.simul_spec
    >>> from padre_meddea.calibration.simul_spec import barium_spectrum, ba133_lines, cd_kalpha1, te_kalpha1
    >>> energy = np.arange(5, 150, 0.3) * u.keV
    >>> flux = barium_spectrum(fwhm = 1 * u.keV)(energy)
    >>> plt.plot(energy, flux, label='Simulated', alpha=0.5, linewidth=3.0)  # doctest: +SKIP
    >>> for i, this_line in enumerate(ba133_lines):
    ...     cd_escape_line = this_line['energy (eV)'] - cd_kalpha1
    ...     te_escape_line = this_line['energy (eV)'] - te_kalpha1
    ...     if cd_escape_line > 0 * u.eV:
    ...         plt.axvline(x=cd_escape_line.to('keV').value, label=f'{cd_escape_line.to("keV"):.2f} Cd escape', color='red')  # doctest: +SKIP
    ...     if te_escape_line > 0 * u.eV:
    ...         plt.axvline(x=te_escape_line.to('keV').value, label=f'{te_escape_line.to("keV"):.2f} Te escape', color='red')  # doctest: +SKIP
    ...     plt.axvline(x=this_line['energy (eV)'].to('keV').value, label=f'{this_line["energy (eV)"].to("keV"):.2f} {this_line["name"]}')
    >>> plt.legend(loc='center left', bbox_to_anchor=(0.60, 0.5))  # doctest: +SKIP
    >>> plt.ylabel('')  # doctest: +SKIP
    >>> plt.xlabel('energy [keV]')  # doctest: +SKIP
    >>> plt.title('Ba-133 Calibration source')  # doctest: +SKIP
