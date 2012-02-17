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

def _pack(filenames, literal_modules):
  out = []
  for filename in filenames:
    _, basename = os.path.split(filename)
    assert basename[:-3] == '.py'
    source = zlib.compress(_readfile(filename))
    out.append('%s\n%d\n%s' % (basename[:-3], len(source), source))
  for name, source in literal_modules:
    source = zlib.compress(source)
    out.append('%s\n%d\n%s' % (name, len(source), source))
  return ''.join(out)

def remote_exec(hostname=None, username=None, port=22,
                ssh_cmd=None, module_filenames=None,
                literal_modules=None):
  if not ssh_cmd:
    if user:
      user = user + '@'
    else:
      user = ''
    ssh_cmd = ['ssh', '-p', str(port), '%s%s' % (user, hostname)]
  main = _pack(module_filenames or [], literal_modules or {})
  stage2 = _readfile('assemble.py')
  stage1 = textwrap.dedent(r'''
      import sys;
      exec compile(sys.stdin.read(%d), "assembler.py", "exec")
      ''') % len(stage2)
  pycmd = ("P=python2; $P -V 2>/dev/null || P=python; "
           "exec \"$P\" -c '%s'") % stage1
  cmd = ['ssh', host, '--', pycmd]

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
  s2.sendall(stage3)
  p.wait()

run('atlas', ['lol.py', 'test.py'])


