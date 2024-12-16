import pathlib
import json

import ee
from ee.oauth import get_credentials_arguments
from qgis.PyQt.QtWidgets import QMessageBox
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

CREDENTIALS_PATH = pathlib.Path('~/.config/earthengine/credentials').expanduser()

def ee_read_config():
    """Reads project name, return None if there is no EE config file detected"""
    try:
        with open(CREDENTIALS_PATH) as json_config_file:
            config = json.load(json_config_file)
    except FileNotFoundError:
        # File may not exist if we initialized from default credentials.
        return None

    return config

def save_project_to_config(project):
    """Write new project name into the EE config file"""
    config = ee_read_config()
    config['project'] = project
    ee.oauth.write_private_json(CREDENTIALS_PATH, config)

def ee_authenticate():
    """ show a dialog to allow users to start or cancel the authentication process """

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

    reply = QMessageBox.warning(None, 'Authenticate Google Earth Engine',
                                msg, QMessageBox.Cancel | QMessageBox.Ok)

    if reply == QMessageBox.Cancel:
        print('Cancel')
        return False
    else:
        ee.Authenticate(auth_mode='localhost', force=True)

        # bug: ee.Authenticate(force=True) returns None, check the auth status manually
        config = ee_read_config()
        if config is not None:
            return True

def get_gcp_projects():
    """
    Fetch a list of Google Cloud projects available to the user using ee.oauth.
    """
    try:
        credentials_args = get_credentials_arguments()

        refresh_token = credentials_args.get("refresh_token")
        token_uri = credentials_args.get("token_uri")
        client_id = credentials_args.get("client_id")
        client_secret = credentials_args.get("client_secret")

        if not refresh_token:
            raise ValueError("Refresh token not found in credentials.")

        credentials = Credentials(
            token=None,  # No access token yet
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
        )

        credentials.refresh(Request())

        service = build('cloudresourcemanager', 'v1', credentials=credentials)

        request = service.projects().list()
        response = request.execute()

        # Parse the response and return active projects
        projects = response.get('projects', [])
        return [project['projectId'] for project in projects if project['lifecycleState'] == 'ACTIVE']

    # TODO: 
    #   The Earth Engine OAuth client is tied to its own Google Cloud project (ID: 517222506229), 
    #   which is used for managing authentication workflows.
    #   However, this project does not inherently have the required permissions or APIs enabled 
    #   (such as the Cloud Resource Manager API) to fetch the list of projects associated with your Google account.
    except Exception as e:
        # Display a warning dialog for any errors
        QMessageBox.warning(None, 'Error', f'Failed to fetch GCP projects: {e}')
        return []
    
def select_gcp_project(projects):
    """Create a dropdown dialog for selecting a GCP project."""
    dialog = QDialog()
    dialog.setWindowTitle("Select Google Cloud Project")
    
    # Set up the layout
    layout = QVBoxLayout()

    # Add dropdown with projects
    dropdown = QComboBox()
    dropdown.addItems(projects)
    layout.addWidget(dropdown)

    # Add OK and Cancel buttons
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    dialog.setLayout(layout)

    # Show the dialog and get the result
    if dialog.exec() == QDialog.Accepted:
        return dropdown.currentText()  # Return selected project
    return None  # Return None if user cancels

def ee_initialize_with_project(project, force=False):
    """Initializes EE with a project or ask user to specify project if there is no project set"""

    msg_no_project = """Google Cloud Project is empty.<br>
    <br>
    Starting November 13, 2024, users will need to use a Google Cloud Project to access the Earth Engine platform.<br>
    See <a href="https://developers.google.com/earth-engine/guides/transition_to_cloud_projects">Transition to Cloud projects</a> for more info.<br>
    <br>
    Make sure your Google Cloud project is registered properly for Earth Engine access<br>
    <br>
    Then set the project name in the text field baloe and click OK or click Cancel to skip<br>
    <br>
    Google Cloud Project:"""

    msg_with_project = """Change Google Cloud project field below to a new value.<br>
    <br>
    Make sure your project is registered properly for Earth Engine access and click OK or click Cancel to skip this step<br>
    <br>
    Google Cloud Project:"""

    if project is None or force:
        projects = get_gcp_projects()  # Fetch the list of available GCP projects
        
        if not projects:
            QMessageBox.warning(None, 'No Projects Found', 'No Google Cloud projects are available. Please ensure your account has access to active projects.')
            return
        
        # Show dropdown to select a project
        selected_project = select_gcp_project(projects)
        if not selected_project:  # User cancelled
            return
        
        project = selected_project  # Update the project with the user's selection

    # Initialize Earth Engine with the selected project
    ee.Initialize(project=project)
    save_project_to_config(project)

def authenticate_and_set_project():
    config = ee_read_config()

    is_authenticated = False

    if config is not None:
        is_authenticated = True

    if not is_authenticated: # not authenticated > start authentication process
        is_authenticated = ee_authenticate()

    # authentication failed
    if not is_authenticated:
        raise ee.EEException("Can not initialize Google Earth Engine. Please make sure you can access Earth Engine, restart QGIS, and re-enable EE plugin.")

    # initialize EE with existing project or select a new one if there is no project
    project = None
    if config is not None:
        project = config.get('project')
    ee_initialize_with_project(project)

def select_project():
    # read existing project
    config = ee_read_config()

    project = None
    if config is not None:
        project = config.get('project')

    ee_initialize_with_project(project, force=True)

