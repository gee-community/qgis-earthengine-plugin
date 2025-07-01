from typing import Optional

import ee
from qgis.PyQt.QtWidgets import QInputDialog, QLineEdit, QMessageBox

from .config import EarthEngineConfig


def ee_authenticate(ee_config: EarthEngineConfig) -> bool:
    """Show a dialog to allow users to start or cancel the authentication process"""

    msg = """This plugin uses Google Earth Engine API and it looks like it is not yet authenticated on this machine.<br>
    <br>
    You need to have a Google account registered for Google Earth Engine access to continue.<br>
    <br>
    Make sure you can access Earth Engine Code Editor by visiting: <br>
    <br>
    <a href="https://code.earthengine.google.com">https://code.earthengine.google.com</a><br>
    <br>
    After validating that you can access Earth Engine, click OK to open a web browser
    and follow the authentication process or click Cancel to skip"""

    reply = QMessageBox.warning(
        None,
        "Authenticate Google Earth Engine",
        msg,
        QMessageBox.Cancel | QMessageBox.Ok,
    )

    if reply == QMessageBox.Cancel:
        print("Cancel")
        return False
    else:
        ee.Authenticate(auth_mode="localhost", force=True)

        # bug: ee.Authenticate(force=True) returns None, check the auth status manually
        return bool(ee_config.read())


def ee_initialize_with_project(ee_config: EarthEngineConfig, force=False) -> None:
    """
    Initialize EE with current project, possibly asking user to specify project if no
    project currently set in configuration or if we force the prompt
    """
    project_id = ee_config.project

    if not project_id or force:
        project_id = prompt_for_project(project_id)
        if not project_id:
            return

    ee.Initialize(project=project_id)
    ee_config.project = project_id


set_project_docs_html = """<br>
    Make sure your Google Cloud project is registered properly for Earth Engine access. To find your Project ID:
    <ul>
        <li> Go to the <a href="https://console.cloud.google.com/">Google Cloud Console</a>. </li>
        <li> Your Project ID is visible in the URL or can be selected from the resource list. </li>
        <li> For more details, refer to the official <a href="https://cloud.google.com/resource-manager/docs/creating-managing-projects">Google Cloud Project Management Guide</a>. </li>
    </ul>"""


def prompt_for_project(cur_project: Optional[str]) -> Optional[str]:
    """Show a dialog to prompt user to specify project"""

    msg_no_project = f"""Google Cloud Project is empty.<br>
    <br>
    Starting November 13, 2024, users will need to use a Google Cloud Project to access the Earth Engine platform.<br>
    See <a href="https://developers.google.com/earth-engine/guides/transition_to_cloud_projects">Transition to Cloud projects</a> for more info.<br>
    {set_project_docs_html}
    Then set the project name in the text field below and click OK or click Cancel to skip.

<br><br><b>Google Cloud Project:</b>"""

    msg_with_project = f"""Change Google Cloud project field below to a new value.<br>
    <br>
    Make sure your project is registered properly for Earth Engine access and click OK or click Cancel to skip this step. <br>
    {set_project_docs_html}
<br><b>Google Cloud Project:</b>"""

    msg = msg_with_project if cur_project else msg_no_project
    (project, _ok) = QInputDialog.getText(
        None, "Select Earth Engine project", msg, QLineEdit.Normal, cur_project
    )
    return project


def ensure_authenticated(ee_config: EarthEngineConfig) -> None:
    """
    Ensure that the user is authenticated with Earth Engine, throwing an exception if not.
    """
    # Trigger authentication if there is no config (ie not authenticated)
    if not ee_config.read():
        auth_success = ee_authenticate(ee_config)

        # authentication failed
        if not auth_success:
            raise ee.EEException(
                "Can not initialize Google Earth Engine. Please make sure you can "
                "access Earth Engine, restart QGIS, and re-enable EE plugin."
            )
