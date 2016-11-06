#!/usr/bin/env python
import BuildTree
import xml.etree.ElementTree as ET
import ParserArgvs
import sys

if __name__ == '__main__':
    args = sys.argv[1:]
    #args = 'SnmpSet -d MoSip attr1 val1 attr2 val2'.split()
    moname = ParserArgvs.Moname(args).moname
    operation = ParserArgvs.Operation(args).oper
    attrs = ParserArgvs.Attrs(args).attrs
    mohead = BuildTree.MoTree(operation,moname,attrs).head
    upmo = BuildTree.UpMoTree(moname)
    upmohead = upmo.head
    upmotail = upmo.tail
    upmotail.append(mohead)
    hello = BuildTree.HelloSession().head
    close = BuildTree.CloseSession().head
    rpctomf = BuildTree.RpctoMF()
    rpctomfhead = rpctomf.head
    rpctomftail = rpctomf.tail
    rpctomftail.append(upmohead)
    print(ET.tostring(rpctomfhead,encoding="utf-8", method="xml"))

