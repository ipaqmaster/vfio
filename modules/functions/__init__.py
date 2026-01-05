#!/usr/bin/env python
import importlib
from os.path import dirname, basename, isfile, join
import glob

# Import all modules of this directory and take their function of the same name.
modules = glob.glob(join(dirname(__file__), "*.py"))
for module in modules:
    if isfile(module) and not module.endswith('__init__.py'):
        moduleName = basename(module)[:-3]
        globals()[moduleName] = getattr(importlib.import_module(f'.{moduleName}', package=__package__), moduleName)
