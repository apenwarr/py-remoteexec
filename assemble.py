import sys

print "STARTED"
sys.stdout.flush()

def _load():
  import imp
  import zlib
  import sys
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
    __log('Read %s (%d bytes)' % (name, n))
  while files:
    for name in list(files.keys()):
      code = compile(files[name], name, 'exec')
      d = {}
      try:
        eval(code, d, d)
      except ImportError:
        continue
      mod = imp.new_module(name)
      mod.__dict__.update(d)
      sys.modules[name] = mod
      __log('Loaded %s' % name)
      del files[name]
  del sys.modules[__name__].__dict__['_load']
  sys.stdout.flush()
  sys.stderr.flush()
  import main
  main.main()
_load()
