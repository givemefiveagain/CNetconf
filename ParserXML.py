#!/usr/bin/env python
"""
the file MGC_mp.xml contains the product infrastruct info including hierarchical relations, attributes of each mo.
using xml.etree.ElementTree package to parse xml, and using collections.defaultdict to store hierarchical relations.
"""
from xml.etree import ElementTree as ET
from collections import defaultdict, deque, Counter

filename = 'MGC_mp.xml'
dbroot = ET.parse(filename).getroot()

class Streams:
    global dbroot
    def __init__(self):
        self._upstream, self._downstream = self.getstreams()
    def getstreams(self):
        upstream = dict()
        downstream = defaultdict(list)
        for containment in dbroot.iter('containment'):
            parent = containment.find('./parent/hasClass').get('name')
            child = containment.find('./child/hasClass').get('name')
            upstream[child] = parent
            downstream[parent].append(child)
        return (upstream, downstream)
    @property
    def upstream(self):
        return self._upstream
    @property
    def downstream(self):
        return self._downstream

class Attributes:
    global dbroot
    def __init__(self):
        self._attrs = self.getattrs()
    def getattrs(self):
        attrs = defaultdict(list)
        for subclass in dbroot.iter('class'):
            for elem in subclass.iter('attribute'):
                attrs[subclass.get('name')].append(elem.get('name'))
        return attrs
    @property
    def attrs(self):
        return self._attrs

class GetMoUpStream:
    def __init__(self,moname):
        self._moname = moname
        self._upstream = self.getUpStream()
        #print(self._moname)
        #print(self._upstream)
    def getUpStream(self):
        tmp = self._moname
        streams = Streams().upstream
        #print(streams)
        upstream = list()
        while tmp in streams.keys():
            val = streams[tmp]
            upstream.append(val)
            tmp = val
        return upstream
    @property
    def upstream(self):
        return self._upstream

class GetAttrs:
    def __init__(self,moname):
        self._moname = moname
        self._attrs = self.getattrs()
    def getattrs(self):
         return Attributes().attrs[self._moname]
    @property
    def attrs(self):
        return self._attrs