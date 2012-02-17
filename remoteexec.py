def _load(verbose):
    import imp
    import sys
    import zlib
    def _log(s):
        sys.stderr.write(s+'\n')
        sys.stderr.flush()
    if verbose:
        log = _log
    else:
        log = lambda _: None
    log('Assembler started')
    files = {}
    decomp = zlib.decompressobj()
    while True:
        name = sys.stdin.readline().strip()
        if not name:
            break
        log('Reading module ' + name)
        n = int(sys.stdin.readline())
        files[name] = decomp.decompress(sys.stdin.read(n))
        log('Read module %s (%d compressed, %d decompressed)'
        % (name, n, len(files[name])))
    log('Finished reading modules, starting compilation')
    while files:
        l = len(files)
        for name in list(files.keys()):
            log('Compiling ' + name)
            code = compile(files[name], name, 'exec')
            d = {}
            try:
                eval(code, d, d)
            except ImportError:
                log("Can't compile %s yet, needs other modules" % name)
                continue
            mod = imp.new_module(name)
            mod.__dict__.update(d)
            sys.modules[name] = mod
            del files[name]
            log('Compiled and loaded ' + name)
        if len(files) == l:
            _log("Infinite compile loop, you're probably missing an import")
            exit(1)
    del sys.modules[__name__].__dict__['_load']
    sys.stdout.flush()
    sys.stderr.flush()
    module, func = sys.stdin.readline().strip().rsplit('.', 2)
    log('All code loaded, sending sync string')
    sys.stdout.write('\0REINDEERFLOTILLA0101')
    sys.stdout.flush()
    log('Sync sent, handing off to %s.%s()' % (module, func))
    sys.modules[module].__dict__[func]()
# END ASSEMBLER
# The above is the stage2 assembler that gets run on the remote
# system. To ensure that syntax errors and exceptions have useful line
# numbers, keep it at the top of the file.

import os
import os.path
import socket
import subprocess
import zlib

# Stage 1 assembler, compiles and executes stage2.
_STAGE1 = '''
import sys;
exec compile(sys.stdin.read(%d), "assembler.py", "exec")
'''
_SYNC_STRING = 'REINDEERFLOTILLA0101'

def _readfile(filename):
    f = open(filename)
    try:
        return f.read()
    finally:
        f.close()

def _pack(filenames, literal_modules, main_func):
    out = []
    compress = zlib.compressobj(9)
    for filename in filenames:
        _, basename = os.path.split(filename)
        assert basename[-3:] == '.py'
        source = compress.compress(_readfile(filename))
        source += compress.flush(zlib.Z_SYNC_FLUSH)
        out.append('%s\n%d\n%s' % (basename[:-3], len(source), source))
    for name, source in literal_modules.iteritems():
        source = compress.compress(source)
        source += compress.flush(zlib.Z_SYNC_FLUSH)
        out.append('%s\n%d\n%s' % (name, len(source), source))
    out.append('\n%s\n' % main_func)
    return ''.join(out)

def _get_assembler(verbose=False):
    filename = __file__
    if filename.endswith('.pyc'):
        filename = filename[:-1]
    source = _readfile(filename)
    assembler = source.split('# END ASSEMBLER\n')[0]
    return '%s\n_load(%s)\n' % (assembler, verbose)

# style guide

class Fatal(Exception):
    pass

def _sync(p, s):
    z = 'x'
    while z and z != '\0':
        z = s.recv(1)
    sync = s.recv(len(_SYNC_STRING))

    ret = p.poll()
    if ret:
        raise Fatal('server died with error code %d' % ret)

    if sync != _SYNC_STRING:
        raise Fatal('expected sync string %s, got %s' % (_SYNC_STRING, sync))

def remote_exec(hostname=None, user=None, port=22,
                ssh_cmd=None, module_filenames=None,
                literal_modules=None, main_func=None,
                verbose_load=False):
    if not ssh_cmd:
        if user:
            user = user + '@'
        else:
            user = ''
        ssh_cmd = ['ssh', '-p', str(port), '%s%s' % (user, hostname)]
    main = _pack(module_filenames or [],
                 literal_modules or {},
                 main_func or 'main.main')
    stage2 = _get_assembler(verbose_load)
    stage1 = _STAGE1 % len(stage2)
    pycmd = ("P=python2; $P -V 2>/dev/null || P=python; "
             "exec \"$P\" -c '%s'") % stage1
    cmd = ssh_cmd + ['--', pycmd]

    (s1,s2) = socket.socketpair()
    sla,slb = os.dup(s1.fileno()), os.dup(s1.fileno())
    s1.close()
    def setup():
        s2.close()
    p = subprocess.Popen(cmd, stdin=sla, stdout=slb,
                         preexec_fn=setup, close_fds=True)
    try:
        os.close(sla)
        os.close(slb)
        s2.sendall(stage2)
        s2.sendall(main)
        _sync(p, s2)
        return p, s2
    except:
        if not p.poll():
            os.kill(p.pid, 9)
            p.wait()
        raise
