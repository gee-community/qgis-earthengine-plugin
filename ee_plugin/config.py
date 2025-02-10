from dataclasses import dataclass, field
import json
from typing import TypedDict, Optional

import ee
from qgis.PyQt.QtCore import QObject, pyqtSignal


class EarthEngineConfigDict(TypedDict):
    project: str


class _ConfigSignals(QObject):
    updated = pyqtSignal(dict, name="newConfig")


@dataclass
class EarthEngineConfig:
    credentials_path: str = field(default_factory=ee.oauth.get_credentials_path)
    signals: _ConfigSignals = field(default_factory=_ConfigSignals, init=False)

    def read(self) -> Optional[EarthEngineConfigDict]:
        """Read the credentials file."""
        try:
            with open(self.credentials_path) as json_config_file:
                return json.load(json_config_file)
        except FileNotFoundError:
            return None

    def _update(self, **updates) -> None:
        current_config = self.read() or {}

        if all(current_config.get(k) == v for k, v in updates.items()):
            return

        updated_config = {**current_config, **updates}
        ee.oauth.write_private_json(self.credentials_path, updated_config)
        self.signals.updated.emit(updated_config)

    @property
    def project(self) -> Optional[str]:
        """Get the current project ID."""
        config = self.read()
        if config:
            return config.get("project")

    @project.setter
    def project(self, project_id: str):
        """Set the current project ID."""
        return self._update(project=project_id)
