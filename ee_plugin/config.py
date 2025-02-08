from dataclasses import dataclass, field
import json
from typing import TypedDict, Optional

import ee
from qgis.PyQt.QtCore import QObject, pyqtSignal


class EarthEngineConfigDict(TypedDict):
    project: str


class ConfigSignals(QObject):
    project_changed = pyqtSignal()


@dataclass
class EarthEngineConfig:
    credentials_path: str = field(default_factory=ee.oauth.get_credentials_path)
    signals: ConfigSignals = field(default_factory=ConfigSignals, init=False)

    def read(self) -> Optional[EarthEngineConfigDict]:
        """Read the credentials file."""
        try:
            with open(self.credentials_path) as json_config_file:
                return json.load(json_config_file)
        except FileNotFoundError:
            return None

    def save_project(self, project: str) -> None:
        """Save project to the credentials file."""
        current_config = self.read() or {}
        if current_config.get("project") == project:
            return
        ee.oauth.write_private_json(
            self.credentials_path,
            {
                **current_config,
                "project": project,
            },
        )
        self.signals.project_changed.emit()

    @property
    def project_id(self) -> Optional[str]:
        """Get the current project ID."""
        config = self.read()
        if config:
            return config.get("project")


ee_config = EarthEngineConfig()
