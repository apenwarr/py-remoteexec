#!/usr/bin/env python

import subprocess
import socket
import os

def pack(modules, main):
  out = []
  for m in modules:
    with open(m) as f:
      content = f.read()
    out.append('%s\n%d\n%s' % (m[:-3], len(content), content))
  out.append('\n')

  return ''.join(out)

def run(host, modules):
  stage3 = pack(modules, None)
  stage2 = open('assemble.py').read()
  stage1 = r'''import sys; exec compile(sys.stdin.read(%d), "assembler.py", "exec");
            ''' % len(stage2)
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

run('localhost', ['lol.py', 'test.py'])
