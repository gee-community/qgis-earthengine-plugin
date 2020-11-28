# -*- coding: utf-8 -*-

import os
import platform
import fnmatch
import zipfile

from paver.easy import *


def get_extlibs():
    if platform.system() == "Windows":
        return 'extlibs_windows'
    if platform.system() == "Darwin":
        return 'extlibs_macos'
    if platform.system() == "Linux":
        return 'extlibs_linux'


options(
    plugin=Bunch(
        name='ee_plugin',
        ext_libs=path(get_extlibs()),
        source_dir=path('.'),
        package_dir=path('.'),
        tests=['test', 'tests'],
        excludes=[
            "*.pyc",
            ".git",
            ".idea",
            ".gitignore",
            ".travis.yml",
            "__pycache__",
            "media",
            "ee_plugin.zip"
        ]
    ),
)


@task
@cmdopts([('clean', 'c', 'clean out dependencies first')])
def setup():
    clean = getattr(options, 'clean', False)
    ext_libs = options.plugin.ext_libs
    if clean:
        ext_libs.rmtree()
    ext_libs.makedirs()
    reqs = read_requirements()
    os.environ['PYTHONPATH'] = ext_libs.abspath()
    for req in reqs:
        if platform.system() == "Windows":
            sh('pip install -U -t "{ext_libs}" "{dep}"'.format(ext_libs=ext_libs.abspath(), dep=req))
        else:
            sh('pip3 install -U -t "{ext_libs}" "{dep}"'.format(ext_libs=ext_libs.abspath(), dep=req))

@task
def install(options):
    '''install plugin to qgis'''
    plugin_name = options.plugin.name
    src = path(__file__).dirname()
    if platform.system() == "Windows":
        dst = path('~/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    if platform.system() == "Darwin":
        dst = path(
            '~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    if platform.system() == "Linux":
        dst = path('~/.local/share/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    src = src.abspath()
    dst = dst.abspath()
    if not hasattr(os, 'symlink'):
        dst.rmtree()
        src.copytree(dst)
    elif not dst.exists():
        src.symlink(dst)


def read_requirements():
    '''return a list of packages in requirements file'''
    with open('requirements.txt') as f:
        return [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#')]


@task
@cmdopts([('tests', 't', 'Package tests with plugin')])
def package(options):
    '''create package for plugin'''
    package_file = options.plugin.package_dir / ('%s.zip' % options.plugin.name)
    with zipfile.ZipFile(package_file, "w", zipfile.ZIP_DEFLATED) as f:
        if not hasattr(options.package, 'tests'):
            options.plugin.excludes.extend(options.plugin.tests)
        make_zip(f, options)


def make_zip(zipFile, options):
    excludes = set(options.plugin.excludes)

    src_dir = options.plugin.source_dir
    exclude = lambda p: any([fnmatch.fnmatch(p, e) for e in excludes])

    def filter_excludes(files):
        if not files: return []
        # to prevent descending into dirs, modify the list in place
        for i in range(len(files) - 1, -1, -1):
            f = files[i]
            if exclude(f):
                files.remove(f)
        return files

    for root, dirs, files in os.walk(src_dir):
        for f in filter_excludes(files):
            relpath = os.path.relpath(root, '.')
            zipFile.write(path(root) / f, path('ee_plugin') / path(relpath) / f)
        filter_excludes(dirs)
