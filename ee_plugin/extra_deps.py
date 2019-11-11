# -*- coding: utf-8 -*-
"""
Install extra plugin dependencies needed for run

All extra packages we need that are generally not part of
QGIS's Python (on Windows) or the system Python (on Linux/macOS).

Some code was based on:
    https://github.com/GIS4WRF/gis4wrf/blob/master/gis4wrf/__init__.py
    https://github.com/GIS4WRF/gis4wrf/blob/master/gis4wrf/bootstrap.py
    https://github.com/GIS4WRF/gis4wrf/blob/master/gis4wrf/plugin/ui/helpers.py
"""
import shutil
import sysconfig
import os, sys, subprocess
import platform
import site
import pkg_resources
from pathlib import Path
from collections import namedtuple

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QVBoxLayout, QProgressBar, QDialog


# Python x.y version tuple, e.g. ('3', '7').
PY_MAJORMINOR = platform.python_version_tuple()[:2]

Dependency = namedtuple('Dep', ['name', 'min', 'install'])

# list of Python packages and versions necessary for this plugin
#   install: fix/exact version number or None
#   min: minimum version number or None
DEPS = [
    Dependency('earthengine-api', install=None, min='0.1.205'),
    Dependency('pyCrypto', install=None, min=None),
]

# Use a custom folder for the packages to avoid polluting the per-user site-packages.
# This also avoids any permission issues.
# Windows: ~\AppData\Local\ee_plugin\python<xy>
# macOS: ~/Library/Application Support/ee_plugin/python<xy>
# Linux: ~/.local/share/ee_plugin/python<xy>
if platform.system() == 'Windows':
    DATA_HOME = os.getenv('LOCALAPPDATA')
    assert DATA_HOME, '%LOCALAPPDATA% not found'
elif platform.system() == 'Darwin':
    DATA_HOME = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
else:
    DATA_HOME = os.getenv('XDG_DATA_HOME')
    if not DATA_HOME:
        DATA_HOME = os.path.join(os.path.expanduser('~'), '.local', 'share')
INSTALL_PREFIX = os.path.join(DATA_HOME, 'ee_plugin', 'python' + ''.join(PY_MAJORMINOR))
LOG_PATH = os.path.join(INSTALL_PREFIX, 'pip.log')


def load_install_extra_deps():
    # Add custom folder to search path.
    for path in site.getsitepackages(prefixes=[INSTALL_PREFIX]):
        if not path.startswith(INSTALL_PREFIX):
            # On macOS, some global paths are added as well which we don't want.
            continue
        yield ('log', 'Added {} as module search path'.format(path))
        # Make sure directory exists as it may otherwise be ignored later on when we need it.
        # This is because Python seems to cache whether module search paths do not exist to avoid
        # redundant lookups.
        os.makedirs(path, exist_ok=True)
        site.addsitedir(path)
        # pkg_resources doesn't listen to changes on sys.path.
        pkg_resources.working_set.add_entry(path)

    installed = []
    needs_install = []
    cannot_update = []
    for dep in DEPS:
        try:
            # Will raise DistributionNotFound if not found.
            location = pkg_resources.get_distribution(dep.name).location
            is_local = Path(INSTALL_PREFIX) in Path(location).parents

            if not dep.min:
                installed.append((dep, is_local))
            else:
                # There is a minimum version constraint, check that.
                try:
                    # Will raise VersionConflict on version mismatch.
                    pkg_resources.get_distribution('{}>={}'.format(dep.name, dep.min))
                    installed.append((dep, is_local))
                except pkg_resources.VersionConflict as exc:
                    # Re-install is only possible if the previous version was installed by us.
                    if is_local:
                        needs_install.append(dep)
                    else:
                        # Continue without re-installing this package and hope for the best.
                        # cannot_update is populated which can later be used to notify the user
                        # that a newer version is required and has to be manually updated.
                        cannot_update.append((dep, exc.dist.version))
                        installed.append((dep, False))

        except pkg_resources.DistributionNotFound as exc:
            needs_install.append(dep)

    if needs_install:
        yield ('needs_install', needs_install)
        yield ('log', 'Package directory: ' + INSTALL_PREFIX)
        # Remove everything as we can't upgrade packages when using --prefix
        # which may lead to multiple pkg-0.20.3.dist-info folders for different versions
        # and that would lead to false positives with pkg_resources.get_distribution().
        if os.path.exists(INSTALL_PREFIX):
            tmp_dir = INSTALL_PREFIX + '_tmp'
            # On Windows, rename + delete allows to re-create the folder immediately,
            # otherwise it may still be locked and we get "Permission denied" errors.
            os.rename(INSTALL_PREFIX, tmp_dir)
            shutil.rmtree(tmp_dir)
        os.makedirs(INSTALL_PREFIX, exist_ok=True)

        # Determine packages to install.
        # Since we just cleaned all packages installed by us, including those that didn't need
        # a re-install, re-install those as well.
        installed_local = [dep for dep, is_local in installed if is_local]
        req_specs = []
        for dep in needs_install + installed_local:
            if dep.install is None:
                req_specs.append(dep.name)
            elif dep.install.startswith('http'):
                req_specs.append(dep.install)
            else:
                req_specs.append('{}=={}'.format(dep.name, dep.install))

        # Locate python in order to invoke pip.
        python = os.path.join(sysconfig.get_path('scripts'), 'python3')

        # Handle the special Python environment bundled with QGIS on Windows.
        try:
            import qgis
        except:
            qgis = None
        if os.name == 'nt' and qgis:
            # sys.executable will be one of two things:
            # within QGIS: C:\Program Files\QGIS 3.0\bin\qgis-bin-g7.4.0.exe
            # within python-qgis.bat: C:\PROGRA~1\QGIS 3.0\apps\Python36\python.exe
            exe_path = sys.executable
            exe_dir = os.path.dirname(exe_path)
            if os.path.basename(exe_path) == 'python.exe':
                python_qgis_dir = os.path.join(exe_dir, os.pardir, os.pardir, 'bin')
            else:
                python_qgis_dir = exe_dir
            python = os.path.abspath(os.path.join(python_qgis_dir, 'python-qgis.bat'))
            if not os.path.isfile(python):
                python = os.path.abspath(os.path.join(python_qgis_dir, 'python-qgis-ltr.bat'))  # for qgis-ltr

        # Must use a single pip install invocation, otherwise dependencies of newly
        # installed packages get re-installed and we couldn't pin versions.
        # E.g. 'pip install pandas==0.20.3' will install pandas, but doing
        #      'pip install xarray==0.10.0' after that would re-install pandas (latest version)
        #      as it's a dependency of xarray.
        # This is all necessary due to limitations of pip's --prefix option.
        args = [python, '-m', 'pip', 'install', '--prefix', INSTALL_PREFIX] + req_specs
        yield ('log', ' '.join(args))
        for line in run_subprocess(args, LOG_PATH):
            yield ('log', line)
        yield ('install_done', None)

    if cannot_update:
        for dep, _ in cannot_update:
            yield ('cannot_update', cannot_update)


class IgnoreKeyPressesDialog(QDialog):
    def keyPressEvent(self, e) -> None:
        # By default, pressing Escape "rejects" the dialog
        # and Enter "accepts" the dialog, closing it in both cases.
        # Overriding this method prevents this behaviour.
        pass


# higher resolution than default (100)
PROGRESS_BAR_MAX = 1000


class WaitDialog(IgnoreKeyPressesDialog):
    def __init__(self, parent, title, progress=False):
        super().__init__(parent, Qt.WindowTitleHint)
        vbox = QVBoxLayout()
        self.progress_bar = QProgressBar()
        max_val = PROGRESS_BAR_MAX if progress else 0
        self.progress_bar.setRange(0, max_val)
        self.progress_bar.setTextVisible(False)
        vbox.addWidget(self.progress_bar)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setLayout(vbox)
        self.setMaximumHeight(0)
        self.setFixedWidth(parent.width() * 0.25)
        self.show()

    def update_progress(self, progress: float) -> None:
        self.progress_bar.setValue(int(progress * PROGRESS_BAR_MAX))
        self.progress_bar.repaint()  # otherwise just updates in 1% steps


def run_subprocess(args, log_path):
    startupinfo = None
    if os.name == 'nt':
         # hides the console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    process = subprocess.Popen(args,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               bufsize=1, universal_newlines=True,
                               startupinfo=startupinfo)
    with open(log_path, 'w') as fp:
        while True:
            line = process.stdout.readline()
            if line != '':
                fp.write(line)
                yield line
            else:
                break
    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, args)

