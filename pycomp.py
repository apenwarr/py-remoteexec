#!/usr/bin/env python

import subprocess
import socket
import os
import os.path
import zlib
import textwrap

def _readfile(filename):
  f = open(filename)
  try:
    return f.read()
  finally:
    f.close()

def _pack(filenames, literal_modules, main_func):
  out = []
  for filename in filenames:
    _, basename = os.path.split(filename)
    assert basename[-3:] == '.py'
    source = zlib.compress(_readfile(filename))
    out.append('%s\n%d\n%s' % (basename[:-3], len(source), source))
  for name, source in literal_modules:
    source = zlib.compress(source)
    out.append('%s\n%d\n%s' % (name, len(source), source))
  out.append('\n%s\n' % main_func)
  return ''.join(out)

def _get_assembler():
  source = _readfile(__file__)
  assembler = source.split('# ' + 'BEGIN ASSEMBLER\n')[1]
  assembler = assembler.split('# ' + 'END ASSEMBLER\n')[0]
  return assembler + '_load()\n'

# BEGIN ASSEMBLER
def _load():
  import imp
  import zlib
  import sys
  files = {}
  while True:
    name = sys.stdin.readline().strip()
    if not name:
      break
    n = int(sys.stdin.readline())
    files[name] = zlib.decompress(sys.stdin.read(n))
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
      del files[name]
  del sys.modules[__name__].__dict__['_load']
  sys.stdout.flush()
  sys.stderr.flush()
  module, func = sys.stdin.readline().strip().rsplit('.', 2)
  sys.modules[module].__dict__[func]()
# END ASSEMBLER

def remote_exec(hostname=None, user=None, port=22,
                ssh_cmd=None, module_filenames=None,
                literal_modules=None, main_func=None):
  if not ssh_cmd:
    if user:
      user = user + '@'
    else:
      user = ''
    ssh_cmd = ['ssh', '-p', str(port), '%s%s' % (user, hostname)]
  main = _pack(module_filenames or [],
               literal_modules or {},
               main_func or 'main.main')
  stage2 = _get_assembler()
  stage1 = textwrap.dedent(r'''
      import sys;
      exec compile(sys.stdin.read(%d), "assembler.py", "exec")
      ''') % len(stage2)
  pycmd = ("P=python2; $P -V 2>/dev/null || P=python; "
           "exec \"$P\" -c '%s'") % stage1
  cmd = ssh_cmd + ['--', pycmd]

  (s1,s2) = socket.socketpair()
  sla,slb = os.dup(s1.fileno()), os.dup(s1.fileno())
  s1.close()
  def setup():
    s2.close()
  # stdout=slb
  p = subprocess.Popen(cmd, stdin=sla, preexec_fn=setup, close_fds=True)
  os.close(sla)
  os.close(slb)
  s2.sendall(stage2)
  s2.sendall(main)
  p.wait()

remote_exec(hostname='localhost',
            module_filenames=['lol.py', 'test.py'],
            main_func='test.hello')
