#!/usr/bin/env python
from ..jModules.Colors  import colors,printer
from ..jModules.Logger  import Logger
import shutil

def check_path_program(name, loglevel=0, verbose=True, logger=None):
    if shutil.which(name):
        if verbose:
            printer(f'%cyan%Is installed: %none%{name}', message_loglevel=1, loglevel=loglevel, logger=None)
        return(True)
    else:
        if verbose:
            printer(f'%red%Is missing:   %none%{name}',  message_loglevel=2, loglevel=loglevel, logger=None)
        return(False)
