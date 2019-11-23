# -*- coding: utf-8 -*-
"""
Init and user authentication in Earth Engine
"""
import webbrowser
from qgis.PyQt.QtWidgets import QInputDialog

import ee


def init():
    try:
        ee.Initialize()
    except ee.ee_exception.EEException:
        authenticate()
        ee.Initialize()  # retry initialization once the user logs in


def authenticate():
    auth_url = ee.oauth.get_authorization_url()
    webbrowser.open_new(auth_url)

    print('\nEarth Engine Authentication:\n'
          'If the web browser does not start automatically, '
          'please manually browse the URL below:\n"{}"'.format(auth_url))

    token, ok = QInputDialog.getText(None, 'Earth Engine Authentication',
                                     'To authorize access needed by Earth Engine, follow the\n'
                                     'instructions and paste the token here:\n\n'
                                     '(If the web browser does not start automatically\n'
                                     'see the python shell).')
    if ok and token:
        ee.oauth._obtain_and_write_token(token.strip())
