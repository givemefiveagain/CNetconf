#!/usr/bin/env python
import xml.etree.ElementTree as ET
import ParserArgvs
import ParserXML
#import BuildXML


class Tree:
    def __init__(self):
        self._head = None
        self._tail = None
    def StreamElement(self,tag):
        root = ET.Element(tag)
        subtag = tag[0].lower() + tag[1:] + 'Id'
        subelem = ET.SubElement(root, subtag)
        subelem.text = '1'
        return root
    @property
    def head(self):
        return self._head
    @property
    def tail(self):
        return self._tail

class StreamTree(Tree):
    def __init__(self,operation='edit-config'):
        self.operation = operation

    def gettail(self):
        pass

class HelloSession(Tree):
    def __init__(self):
        self._head = ET.Element('hello',{'xmlns':"urn:ietf:params:xml:ns:netconf:base:1.0"})
        self._tail = ET.SubElement(self._head,'capabilities')
        ET.SubElement(self._tail,'capability').text = 'urn:ietf:params:netconf:base:1.0'

class CloseSession(Tree):
    def __init__(self):
        self._head = ET.Element('rpc',{'message-id':'100','xmlns':"urn:ietf:params:xml:ns:netconf:base:1.0"})
        self._tail = ET.SubElement(self._head,'close-session')

class RpctoMF(Tree):
    def __init__(self):
        self._head = ET.Element('rpc',{'message-id':'1','xmlns':"urn:ietf:params:xml:ns:netconf:base:1.0"})
        self.configtomf()
    def configtomf(self):
        edit_config = ET.SubElement(self._head,'edit-config')
        target = ET.SubElement(edit_config, 'target')
        ET.SubElement(target, 'running')
        config = ET.SubElement(edit_config, 'config',{'xmlns:xc':"urn:ietf:params:xml:ns:netconf:base:1.0"})
        me = ET.SubElement(config,'ManagedElement',{'xmlns':"urn:com:ericsson:ecim:ComTop"} )
        ET.SubElement(me,'managedElementId' ).text = '1'
        self._tail = ET.SubElement(me, 'ManagedFunction',{'xmlns':"urn:com:ericsson:ecim:ManagedFunction"})
        ET.SubElement(self._tail,'managedFunctionId').text = '1'

class UpMoTree(Tree):
    def __init__(self,moname):
        super(UpMoTree,self).__init__()
        self._moname = moname
        self._upstream = ParserXML.GetMoUpStream(self._moname).upstream[:-2]
        ##[:-2] ##subtract 'ManagedFunction', 'ManagedElement'
        self.gethead()
    def gethead(self):
        upstream = self._upstream[::-1] ##reverse
        #print('upstream is {}'.format(upstream))
        self._head = self.StreamElement(upstream[0])
        root = self._head
        sindex = 1
        while sindex < len(upstream):
            child = self.StreamElement(upstream[sindex])
            root.append(child)
            root = child
            sindex += 1
        self._tail = child
        #print(ET.tostring(self._tail))

class MoTree(Tree):
    def __init__(self,oper,moname,attrs):
        self._oper = oper
        self._moname = moname
        self._attrs = attrs
        self.gethead()
    def gethead(self):
        self._head = ET.Element(self._moname,{'operation':self._oper})
        sindex = 0
        while sindex < len(self._attrs):
            self._tail = ET.SubElement(self._head,self._attrs[sindex])
            self._tail.text = self._attrs[sindex+1]
            sindex += 2


#"""
if __name__ == '__main__':
    #upmo = UpMoTree('MoSip')
    #head, tail = upmo.head ,upmo.tail

    print(ET.tostring(UpMoTree('MoSip').head))
    #print(ET.tostring(tail))
#"""




