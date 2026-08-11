"""Tests for AWS database helpers using the moto-backed Timestream mock."""

import os
from unittest.mock import MagicMock

import boto3
import numpy as np
import pytest
from astropy import units as u
from astropy.time import Time
from astropy.timeseries import TimeSeries
from moto import mock_aws

import padre_meddea.io.aws_db as aws_db


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def mocked_timestream(aws_credentials):
    """Create a mocked Timestream database and table for tests."""
    with mock_aws():
        client = boto3.client("timestream-write", region_name="us-east-1")
        database_name = "dev-padre_sdc_aws_logs"
        table_name = "dev-padre_measures_table"
        client.create_database(DatabaseName=database_name)
        client.create_table(
            DatabaseName=database_name,
            TableName=table_name,
            RetentionProperties={
                "MemoryStoreRetentionPeriodInHours": 24,
                "MagneticStoreRetentionPeriodInDays": 7,
            },
        )
        yield client


def test_record_housekeeping_uses_mock_timestream(monkeypatch, mocked_timestream):
    """record_housekeeping should complete without error and preserve the expected data columns."""
    hk_ts = TimeSeries(time=[Time("2026-08-05T00:00:00")])
    hk_ts["fp_temp"] = [10.0] * u.K
    hk_ts["hvps_temp"] = [11.0] * u.K
    hk_ts["dib_temp"] = [12.0] * u.K
    hk_ts["CCSDS_APID"] = [0]
    hk_ts["timestamp"] = [0]
    hk_ts["CHECKSUM"] = [0]
    hk_ts.meta["ORIGFILE"] = "example.fits"

    recorded = {}

    def fake_record_timeseries(ts, table, mission):
        recorded["ts"] = ts
        recorded["table"] = table
        recorded["mission"] = mission

    monkeypatch.setattr(aws_db, "create_annotation", lambda *args, **kwargs: None)
    monkeypatch.setattr(aws_db, "record_timeseries", fake_record_timeseries)
    aws_db.record_housekeeping(hk_ts)

    assert recorded["table"] == "housekeeping"
    assert recorded["mission"] == "meddea"
    assert "cal_fp_temp" in recorded["ts"].colnames
    assert recorded["ts"]["fp_temp"][0] == 10.0 * u.K
    assert recorded["ts"].meta["ORIGFILE"] == "example.fits"


def test_record_cmd_uses_mock_timestream(monkeypatch, mocked_timestream):
    """record_cmd should complete without error and preserve the command data."""
    cmd_ts = TimeSeries(time=[Time("2026-08-05T00:00:00")])
    cmd_ts["cmd"] = ["TEST"]
    cmd_ts.meta["ORIGFILE"] = "example.fits"

    recorded = {}

    def fake_record_timeseries(ts, table, mission):
        recorded["ts"] = ts
        recorded["table"] = table
        recorded["mission"] = mission

    monkeypatch.setattr(aws_db, "create_annotation", lambda *args, **kwargs: None)
    monkeypatch.setattr(aws_db, "record_timeseries", fake_record_timeseries)
    aws_db.record_cmd(cmd_ts)

    assert recorded["table"] == "cmd_resp"
    assert recorded["mission"] == "meddea"
    assert recorded["ts"]["cmd"][0] == "TEST"
    assert recorded["ts"].meta["ORIGFILE"] == "example.fits"


def test_record_filename_uses_mock_timestream(monkeypatch, mocked_timestream):
    """record_filename should complete without error and preserve the filename metadata."""
    recorded = {}

    def fake_record_timeseries(ts, table, mission):
        recorded["ts"] = ts
        recorded["table"] = table
        recorded["mission"] = mission

    monkeypatch.setattr(aws_db, "create_annotation", lambda *args, **kwargs: None)
    monkeypatch.setattr(aws_db, "record_timeseries", fake_record_timeseries)
    start = Time("2026-08-05T00:00:00")
    end = Time("2026-08-05T00:01:00")

    aws_db.record_filename(
        filename="padre_meddea_l0_photon_20260805T000000_v1.0.0.fits",
        start_time=start,
        end_time=end,
        level_str="l0",
    )

    assert recorded["table"] == "files_l0"
    assert recorded["mission"] == "meddea"
    assert (
        recorded["ts"]["filename"][0]
        == "padre_meddea_l0_photon_20260805T000000_v1.0.0.fits"
    )
    assert "l0/photon/2026/08/05" in recorded["ts"]["url"][0]


def test_record_photons_uses_mock_timestream(monkeypatch, mocked_timestream):
    """record_photons should complete without error and preserve the expected photon data."""
    ph_list = MagicMock()
    ph_list.time = np.array([Time("2026-08-05T00:00:00")])
    ph_list.meta = {"ORIGFILE": "example.fits"}
    ph_list.calibrate = lambda: None
    ph_list.lightcurve.return_value = TimeSeries(time=[Time("2026-08-05T00:00:00")])
    ph_list.lightcurve.return_value["counts"] = [1]

    recorded = {}

    def fake_record_timeseries(ts, table, mission):
        recorded["ts"] = ts
        recorded["table"] = table
        recorded["mission"] = mission

    monkeypatch.setattr(aws_db, "create_annotation", lambda *args, **kwargs: None)
    monkeypatch.setattr(aws_db, "record_timeseries", fake_record_timeseries)
    aws_db.record_photons(ph_list)

    assert recorded["table"] == "spectra"
    assert recorded["mission"] == "meddea"
    assert recorded["ts"]["counts"][0] == 1
    assert recorded["ts"].time[0] == Time("2026-08-05T00:00:00")
