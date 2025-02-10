import json
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pytest

from ee_plugin import config


@pytest.fixture
def conf():
    with NamedTemporaryFile(mode="w") as f:
        json.dump({"project": "qgis-testing"}, f)
        f.flush()
        yield config.EarthEngineConfig(credentials_path=f.name)


def test_config_read_project(conf: config.EarthEngineConfig):
    """
    Ensure project ID correctly read from the credentials file.
    """
    assert conf.project == "qgis-testing", "Project ID not set correctly."


def test_config_write_project(conf: config.EarthEngineConfig):
    """
    Ensure project ID correctly written to the credentials file.
    """
    conf.project = "new-project"
    assert conf.project == "new-project", "Project ID not set correctly."
    with open(conf.credentials_path, "r") as f:
        assert (
            json.load(f)["project"] == "new-project"
        ), "Project ID not written correctly."


def test_config_project_signal(conf: config.EarthEngineConfig):
    """
    Ensure signal emitted when project written to the credentials file.
    """
    m = MagicMock()

    conf.signals.updated.connect(m)

    m.assert_not_called(), "Signal emitted before change."

    conf.project = "new-project"

    m.assert_called_once_with({"project": "new-project"}), "Signal not emitted."
