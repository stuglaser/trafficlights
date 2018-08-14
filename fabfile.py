from __future__ import with_statement, absolute_import
from fabric.api import run, cd, sudo, put, env
from fabric.contrib import files

env.use_ssh_config = True

def setup_nanomsg():
    VSN = '0.4-beta'
    RELEASE = 'nanomsg-%s' % VSN
    TARBALL = '%s.tar.gz' % VSN
    sudo("apt-get -y install automake libtool build-essential python-pip")
    if not files.exists(TARBALL):
        run('wget https://github.com/nanomsg/nanomsg/archive/%s' % TARBALL)
    if not files.exists(RELEASE):
        run('tar -xzf %s' % TARBALL)
    if not files.exists("%s/nanocat" % RELEASE):
        with cd(RELEASE):
            run('./autogen.sh')
            run('./configure')
            run('make')
            sudo('make install')
            sudo('ldconfig')


def setup():
    setup_nanomsg()
    sudo('pip install nanomsg')
    sudo('pip install RPi.GPIO')
    sudo('pip install termcolor')
    sudo('pip install chan')


def deploy():
    run('hostname')
    if files.exists("/etc/init.d/traffic"):
        sudo('/etc/init.d/traffic stop', pty=False)
    put('traffic.py')
    put('lights.py')
#    put('run.sh')
#    put('init-%s' % env.host_string, '/etc/init.d/traffic', use_sudo=True)
#    sudo('chown root:root /etc/init.d/traffic')
#    sudo('update-rc.d traffic defaults')
#    sudo('chmod 755 /etc/init.d/traffic')
#    sudo('/etc/init.d/traffic start', pty=False)
