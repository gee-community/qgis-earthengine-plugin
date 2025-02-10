import json
from tempfile import TemporaryFile

from ee_plugin import config


def test_config():
    with TemporaryFile("w") as f:
        json.dump({"project": "qgis-testing"}, f)
        conf = config.EarthEngineConfig(credentials_path=f.name)

        assert conf.project_id == "qgis-testing", "Project ID not set correctly."
