from unittest.mock import MagicMock

import pytest
from qgis.PyQt.QtWidgets import QMessageBox

from ee_plugin.config import EarthEngineConfig
from ee_plugin import ee_auth


@pytest.fixture
def auth_config(tmp_path):
    return EarthEngineConfig(credentials_path=str(tmp_path / "credentials"))


class FakeProgressDialog:
    def __init__(self, *_, **__):
        self.closed = False

    def setWindowTitle(self, *_):
        pass

    def setWindowModality(self, *_):
        pass

    def setMinimumDuration(self, *_):
        pass

    def show(self):
        pass

    def wasCanceled(self):
        return False

    def close(self):
        self.closed = True


def test_ee_authenticate_returns_false_when_localhost_auth_times_out(
    monkeypatch, auth_config
):
    monkeypatch.setattr(
        ee_auth.QMessageBox,
        "warning",
        MagicMock(return_value=QMessageBox.StandardButton.Ok),
    )
    monkeypatch.setattr(ee_auth, "QProgressDialog", FakeProgressDialog)
    monkeypatch.setattr(ee_auth.QCoreApplication, "processEvents", MagicMock())
    monkeypatch.setattr(ee_auth.webbrowser, "open_new", MagicMock(return_value=True))
    monkeypatch.setattr(ee_auth, "AUTH_TIMEOUT_SECONDS", 0)

    assert ee_auth.ee_authenticate(auth_config) is False


def test_ee_authenticate_does_not_start_auth_when_user_cancels(
    monkeypatch, auth_config
):
    authenticate = MagicMock()
    monkeypatch.setattr(ee_auth, "_authenticate_localhost", authenticate)
    monkeypatch.setattr(
        ee_auth.QMessageBox,
        "warning",
        MagicMock(return_value=QMessageBox.StandardButton.Cancel),
    )

    assert ee_auth.ee_authenticate(auth_config) is False
    authenticate.assert_not_called()
