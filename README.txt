Remote Exec lets you ship python code to a remote machine and run it
there, all without installing anything other than the standard Python
interpreter on the server.

It connects to the remote host using SSH, sends the python files you
specify, compiles them on the server, and passes control to the
specified main function.

Additionally, the client arranges for stdin/stdout on the server side
to be connected to a network socket on the client side, so that you
can communicate with the uploaded server binary as if you'd connected
to it normally.

What this lets you do is ensure that the server end of your software
is never out of date, since it'll always be in sync with the client
code you're running.

The original idea came from Avery Pennarun's awesome sshuttle
(http://github.com/apenwarr/sshuttle), which uses this great hack to
function with any server that has Python installed (i.e. all of
them).

His original version smushed all files into a single namespace,
however while I was factoring it out of sshuttle he came up with the
compile/eval/__dict__.update hack that allows reconstruction of the
original module structure on the server, neatly avoiding the need for
the skip_imports hack sshuttle uses. I took it from there and
implemented it as a reusable library.
