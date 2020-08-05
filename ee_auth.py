# -*- coding: utf-8 -*-
"""
Init and user authentication in Earth Engine
"""
import os
import hashlib
import urllib.request
import webbrowser
from qgis.PyQt.QtWidgets import QInputDialog

import ee
import logging

# fix the warnings/errors messages from 'file_cache is unavailable when using oauth2client'
# https://github.com/googleapis/google-api-python-client/issues/299
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


def init():
    try:
        ee.Initialize()
    except ee.ee_exception.EEException:
        if authenticate():
            ee.Initialize()  # retry initialization once the user logs in
        else:
            print('\nGoogle Earth Engine authorization failed!\n')


def tiny_url(url):
    try:
        apiurl = "http://tinyurl.com/api-create.php?url="
        tinyurl = urllib.request.urlopen(apiurl + url).read()
        return True, tinyurl.decode("utf-8")
    except:
        return False, url


def authenticate():
    # PKCE.  Generates a challenge that the server will use to ensure that the
    # auth_code only works with our verifier.  https://tools.ietf.org/html/rfc7636
    code_verifier = ee.oauth._base64param(os.urandom(32))
    code_challenge = ee.oauth._base64param(hashlib.sha256(code_verifier).digest())
    auth_url = ee.oauth.get_authorization_url(code_challenge)
    tiny_url_ok, auth_url = tiny_url(auth_url)

    webbrowser.open_new(auth_url)

    print('\nGoogle Earth Engine Authorization:\n'
          'If the web browser does not start automatically, '
          'start it manually and open the following URL:\n"{}"'.format(auth_url))

    token, ok = QInputDialog.getText(None, 'Authorization',
                                     'Google Earth Engine Python is not detected on this machine.\n'
                                     'This plugin uses Google Earth Engine Python API and requires\n'
                                     'users to be authorized, please follow the instructions in the\n'
                                     'opened web page and paste the resulting auth token here.\n\n'
                                     'If the web page does not open automatically,\n'
                                     + ('visit the following link manually:\nURL: {}'.format(auth_url)
                                     if tiny_url_ok else 'visit the link that appears in the python console'))

    if ok and token:
        ee.oauth._obtain_and_write_token(token.strip(), code_verifier)
        return True
    else:
        return False
