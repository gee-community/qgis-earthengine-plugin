#!/usr/bin/env python
"""
Class and function of the GEE datasets
"""


class Dataset(object):
    instances = []

    def __init__(self):
        #
        self.name = None
        self.url = None
        #
        self.availability = None  # {from: date, to: date}
        self.description = None
        self.provider = None
        self.bands = None
        self.tags = None
        self.thumbnails = None

        Dataset.instances.append(self)


