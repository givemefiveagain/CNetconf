#!/usr/bin/env python
"""
This module is used to parse input argument from user.
initial trial, I try to use the argparse module from Python library, but it fails.
because the input is moname and parameters of it, which are  variable, not constant.

the user input format:
script_name.py snmpSet [-u|-d] Moname attr1 val1 attr2 val2 ... ...
script_name.py [create|delete|merge] Moname attr1 val1 attr2 val2 ... ...
script_name.py get Moname [attr1 val1 attr2 val2 ... ...]
script_name.py getall

this module is to parse the user input, and get
1. Moname
2. operation: create|delete|merge|get|getall
3. attrs: it depends on Moname and operation
"""

class Argvs:
    def __init__(self, argvs):
        self.argvs = argvs

class Moname(Argvs):
    def __init__(self,argvs):
        super(Moname,self).__init__(argvs)
        self._mo = self.getmoname()
    def getmoname(self):
        self._mo = None
        for arg in self.argvs:
            if arg.startswith('Mo'):
                self._mo = arg
                break
        return self._mo
    @property
    def moname(self):
        return self._mo



class Operation(Argvs):
    def __init__(self,argvs):
        super(Operation,self).__init__(argvs)
        self._oper = self.getoperation()
    def getoperation(self):
        oper = None
        for arg in self.argvs:
            if arg.startswith('snmpSet'):
                continue
            elif arg.startswith('-'):
                if arg == '-u':
                    oper = 'merge'
                elif arg == '-d':
                    oper = 'delete'
                else:
                    oper = 'create'
                break
            elif arg == 'create':
                oper = arg
                break
            elif arg == 'merge':
                oper = arg
                break
            elif arg == 'delete':
                oper = arg
                break
            elif arg.startswith('get'):
                oper = arg
                break
        return oper
    @property
    def oper(self):
        return self._oper

class Attrs(Argvs):
    def __init__(self,argvs):
        super(Attrs,self).__init__(argvs)
        self._attrs = self.getattrs()
    def getattrs(self):
        self._attrs = None
        for arg in self.argvs:
            if arg.startswith('Mo'):
                index = self.argvs.index(arg)
                self._attrs = self.argvs[index+1:]
                break
            elif arg.startswith('getall'):
                break
        return self._attrs
    @property
    def attrs(self):
        return self._attrs





"""
if __name__ == '__main__':
    args = Moname('snmpSet -d MoSipProfile ip 10.170.9.125 state active'.split())
    tabname,operation,attrs = args.TabOperAttrs()
    print('tabname is ',tabname)
    print('operation is ',operation)
    print('attrs is ',attrs)
"""