#!/usr/bin/env python
import subprocess
import os

is_root = os.geteuid() == 0

try: # Consider supporting doas as well?
    subprocess.run(['sudo', '--version'], capture_output=True, text=True, check=True)
    _run_cmd_sudo_available = True
except subprocess.CalledProcessError:
    _run_cmd_sudo_available = False
    print('Sudo isn\'t installed.') # Replace this entire block with a cleaner check for all deps
    exit(5)

def run_cmd(command: list, sudo=False, decode='utf-8'):

    # Use sudo if requested and not already root
    # Again, consider supporting doas
    if sudo and not is_root:
        command = ['sudo'] + command

    try:
        result = subprocess.run(command, capture_output=True, shell=True, text=False)
        if decode:
            result.stdout = result.stdout.decode(decode)
            result.stderr = result.stderr.decode(decode)
        return result.returncode, result.stdout, result.stderr
    except Exception as e: 
        print(f'Couldn\'t run command: {command}')
        print(e)

