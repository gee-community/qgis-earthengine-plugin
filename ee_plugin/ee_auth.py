import http.server
import time
import urllib.parse
import webbrowser
from typing import Optional

import ee
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QProgressDialog

from .config import EarthEngineConfig

AUTH_TIMEOUT_SECONDS = 300


class AuthenticationCanceled(Exception):
    """Raised when the interactive authentication flow is canceled or expires."""


def _write_token(
    ee_config: EarthEngineConfig,
    auth_code: str,
    code_verifier: str,
    redirect_uri: str,
) -> None:
    refresh_token = ee.oauth.request_token(
        auth_code.strip(),
        code_verifier,
        redirect_uri=redirect_uri,
    )
    credentials = {
        "refresh_token": refresh_token,
        "scopes": ee.oauth.SCOPES,
    }
    project = ee.oauth._project_number_from_client_id(credentials.get("client_id"))
    if project:
        credentials["project"] = project
    ee.oauth.write_private_json(ee_config.credentials_path, credentials)


def _authenticate_localhost(ee_config: EarthEngineConfig) -> None:
    """Run localhost auth with a cancelable Qt wait loop.

    ee.Authenticate(auth_mode="localhost") blocks forever waiting for the OAuth
    callback. Owning the local server here keeps QGIS responsive if the user
    closes the browser before completing sign-in.
    """

    code = None
    auth_error = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # pylint: disable=invalid-name
            nonlocal auth_error, code
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code = query.get("code", [None])[0]
            auth_error = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            if code:
                self.wfile.write(
                    b"\n\nGoogle Earth Engine authorization successful!\n\n"
                    b"Credentials have been retrieved. You can close this window.\n"
                )
            else:
                self.wfile.write(
                    b"\n\nGoogle Earth Engine authorization did not complete.\n\n"
                    b"Return to QGIS and start sign-in again.\n"
                )

        def log_message(self, *_) -> None:
            pass

    try:
        server = http.server.HTTPServer(
            ("localhost", ee.oauth.DEFAULT_LOCAL_PORT), Handler
        )
    except OSError:
        server = http.server.HTTPServer(("localhost", 0), Handler)
    server.timeout = 0.25
    redirect_uri = f"http://localhost:{server.server_address[1]}"

    pkce = ee.oauth._nonce_table("code_verifier")
    auth_url = ee.oauth.get_authorization_url(
        pkce["code_challenge"], ee.oauth.SCOPES, redirect_uri
    )

    progress = QProgressDialog(
        "Complete Google Earth Engine sign-in in your browser.",
        "Cancel",
        0,
        0,
        None,
    )
    progress.setWindowTitle("Authenticate Google Earth Engine")
    window_modality = getattr(Qt, "WindowModality", Qt).ApplicationModal
    progress.setWindowModality(window_modality)
    progress.setMinimumDuration(0)
    progress.show()

    webbrowser.open_new(auth_url)
    deadline = time.monotonic() + AUTH_TIMEOUT_SECONDS

    try:
        while not code:
            QCoreApplication.processEvents()
            if auth_error:
                raise AuthenticationCanceled(f"Authentication failed: {auth_error}")
            if progress.wasCanceled():
                raise AuthenticationCanceled("Authentication canceled.")
            if time.monotonic() >= deadline:
                raise AuthenticationCanceled("Authentication timed out.")
            server.handle_request()

        _write_token(ee_config, code, pkce["code_verifier"], redirect_uri)
    finally:
        progress.close()
        server.server_close()


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
        QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
    )

    if reply == QMessageBox.StandardButton.Cancel:
        print("Cancel")
        return False

    try:
        _authenticate_localhost(ee_config)
    except AuthenticationCanceled:
        return False

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
        None, "Select Earth Engine project", msg, QLineEdit.EchoMode.Normal, cur_project
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
