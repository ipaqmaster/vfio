#!/usr/bin/env python
from ..jModules.Colors  import colors,printer



def cpu_threads():
    with open('/proc/cpuinfo', 'r') as f:
        cpuinfo_contents = f.read()
    
    cpu_threads = {}
    physical_id = core_id = apicid = None
    for line in cpuinfo_contents.split('\n'):
    
        if not line:
            physical_id = core_id = apicid = None
    
        line_value = line.split(' ')[-1]
        if line.startswith('physical id'):
            physical_id = line_value
    
        if line.startswith('core id'):
            core_id = line_value
    
        if line.startswith('processor'):
            processor = line_value
    
        if physical_id and core_id and processor:
            if not physical_id in cpu_threads:
                cpu_threads[physical_id] = {}
    
            if not core_id in cpu_threads[physical_id]:
                cpu_threads[physical_id][core_id] = []
    
            if physical_id and core_id:
                cpu_threads[physical_id][core_id].append(processor)
    
            physical_id = core_id = apicid = None
    
    def printDicts(Dict, indent=0):
        for key, value in Dict.items():
            if type(value) == dict:
                printer(key, loglevel=1, indent=indent)
                printDicts(value, indent=indent+1)
            else:
                printer(f'{key}: {value}', loglevel=1, indent=indent)
    
        if indent <= 2:
            printer('', loglevel=1)
    
    printDicts(cpu_threads)
