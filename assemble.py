import imp
import StringIO
import sys
import os
import threading
import zlib

def __load():
  def __log(s):
    print s
    sys.stdout.flush()

  files = {}

  while True:
    name = sys.stdin.readline().strip()
    if not name:
      break
    n = int(sys.stdin.readline())
    files[name] = zlib.decompress(sys.stdin.read(n))

  n = len(files)
  while len(files) != n:
    n = len(files)

    for name, source in files:
      try:
        code = compile(source, name, 'exec')
      except ImportError:
        continue
      d = {}
      eval(code, d, d)
      mod = imp.new_module(name)
      mod.__dict__.update(d)
      sys.modules[name] = mod


sys.stderr.flush()
sys.stdout.flush()
