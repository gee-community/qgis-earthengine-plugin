# -*- coding: utf-8 -*-

import os
import sys
import fnmatch
import zipfile
import json
from collections import defaultdict

# this pulls in the sphinx target
from paver.easy import *
from paver.doctools import html


def get_extlibs():
    if os.name == 'nt':
        return 'ee_plugin/extlibs_windows'
    elif sys.platform == 'darwin':
        return 'ee_plugin/extlibs_macos'
    else:
        return 'ee_plugin/extlibs_linux'


options(
    plugin=Bunch(
        name='ee_plugin',
        ext_libs=path(get_extlibs()),
        source_dir=path('ee_plugin'),
        package_dir=path('.'),
        tests=['test', 'tests'],
        excludes=[
            '*.pyc',
            ".git"
        ]
    ),

    sphinx=Bunch(
        docroot=path('help'),
        sourcedir=path('help/source'),
        builddir=path('help/build')
    )
)


@task
@cmdopts([
    ('clean', 'c', 'clean out dependencies first'),
])
def setup():
    clean = getattr(options, 'clean', False)
    ext_libs = options.plugin.ext_libs
    if clean:
        ext_libs.rmtree()
    ext_libs.makedirs()
    reqs = read_requirements()
    os.environ['PYTHONPATH'] = ext_libs.abspath()
    for req in reqs:
        if os.name == 'nt':
            sh('pip install -U -t %(ext_libs)s %(dep)s' % {
                'ext_libs': ext_libs.abspath(),
                'dep': req
            })
        else:
            sh('pip3 install -U -t %(ext_libs)s %(dep)s' % {
                'ext_libs': ext_libs.abspath(),
                'dep': req
            })


def read_requirements():
    '''return a list of runtime and list of test requirements'''
    lines = open('requirements.txt').readlines()
    lines = [l for l in [l.strip() for l in lines] if l]
    return [l for l in lines if l[0] != '#']


@task
@cmdopts([
    ('tests', 't', 'Package tests with plugin')
])
def package(options):
    '''create package for plugin'''
    #builddocs(options) TODO
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
            zipFile.write(path(root) / f, path(relpath) / f)
        filter_excludes(dirs)

    for root, dirs, files in os.walk(options.sphinx.builddir):
        for f in files:
            relpath = os.path.join(options.plugin.name, "help", os.path.relpath(root, options.sphinx.builddir))
            zipFile.write(path(root) / f, path(relpath) / f)
