.. _customization:

**************************************
Customization and Global Configuration
**************************************

The :file:`config.yml` file
============================

``padre_meddea`` does not maintain its own configuration file. Instead, it uses
the shared `swxsoc <https://swxsoc.readthedocs.io>`__ package's :file:`config.yml`
configuration file, which is loaded automatically as ``padre_meddea.config``
(a plain `dict`) when the package is imported. You can see the path to the
active configuration file, as well as its contents, by running::

    >>> import padre_meddea
    >>> padre_meddea.print_config()  # doctest: +SKIP

For a full description of how to locate, customize, and override the
:file:`config.yml` file (including per-mission configuration and the
``SWXSOC_CONFIGDIR``/``SWXSOC_MISSION`` environment variables), see the
`swxsoc customization guide <https://swxsoc.readthedocs.io/en/latest/user-guide/customization.html>`__.

Sample data download directory
===============================

Sample data files (see :mod:`padre_meddea.data.sample`) are cached locally so
they only need to be downloaded once. By default they are stored in
``~/.padre_meddea/data``. This can be overridden programmatically by setting
``download_dir`` under the ``downloads`` key of ``padre_meddea.config``, for
example::

    >>> import padre_meddea
    >>> padre_meddea.config.setdefault("downloads", {})["download_dir"] = "/home/user/Downloads"  # doctest: +SKIP

.. note::
    This override is not currently a documented field in swxsoc's
    :file:`config.yml` schema, so it must be set at runtime as shown above.
    Support for configuring it directly in :file:`config.yml` may be added in
    a future release.
