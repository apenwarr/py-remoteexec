#!/usr/bin/env python

import socket
import sys

mods = {
    'test1': '\n'.join([
        'import test',
        'import test2',
        'def print_stuff():',
        '  print "Hello from test1"',
        '  print test2.hello',
        '  print test.mods',
        '  test.hostname()',
        ]),
    'test2': '\n'.join([
        'hello = "Hello from test2"',
        ]),
    }

def hostname():
  print socket.gethostname()

if __name__ == '__main__':
  import pycomp
  pycomp.remote_exec(hostname=sys.argv[1],
                     module_filenames=['test.py', 'pycomp.py'],
                     literal_modules=mods,
                     main_func='test1.print_stuff')
