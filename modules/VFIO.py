#!/usr/bin/env python
from .functions       import *
from .jModules.Colors import colors,printer
from .jModules.Logger import Logger
import os

#Usage:
#   from modules.VFIO import VFIO
#   vfio = VFIO(config=configDict)
#   vfio.run()

_scriptRoot = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_scriptName = _scriptRoot.split('/')[-1]
_namespace  = _scriptName
configFile  = "%s/config.json" % _scriptRoot
schemaFile  = "%s/schema.json" % _scriptRoot
os.chdir(_scriptRoot)

class VFIO:
    def __init__(self, args):

        self.args = args

        self.logger = Logger()

    def run(self):
        print('Stub commit.')
        print('Soon this will do something.')
        result = run_cmd('date'.split(' '))
        print(result[1])
        check_path_program('sudo')
        check_path_program('bash')
        check_path_program('date')
        check_path_program('file')
        check_path_program('tegsd')
