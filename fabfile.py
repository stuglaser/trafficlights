
from __future__ import with_statement, absolute_import
from fabric.api import run, cd, sudo, put, env
from fabric.contrib import files

env.use_ssh_config = True

def setup_nanomsg():
    VSN = '0.4-beta'
    RELEASE = 'nanomsg-%s' % VSN
    TARBALL = '%s.tar.gz' % VSN
    sudo("apt-get -y install automake libtool build-essential python-pip avahi-utils")
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


def update_hostname(name):
    name = "%s.local" % name
    sudo("grep %s /etc/hostname || (echo %s > /etc/hostname && hostname %s && service avahi-daemon restart)" % (name, name, name))

def deploy(*args, **kwargs):
    deploy_context = {
        'brain': '',
        'controls': ''
    }
    if 'brain' in kwargs:
        deploy_context['brain'] = kwargs['brain']
        if 'node' in kwargs:
            update_hostname("traffic-node-%s" % kwargs['node'])
        else:
            update_hostname("traffic-node")
    else:
        update_hostname('traffic-brain')

    if 'controls' in kwargs:
        if kwargs['controls'].lower() == 'yes':
            deploy_context['controls'] = 'yes'
        else:
            deploy_context['controls'] = 'no'

    run('hostname')
    if files.exists("/etc/init.d/traffic"):
        sudo('/etc/init.d/traffic stop', pty=False)
    put('traffic.py')
    put('lights.py')
    put('run.sh')
    files.upload_template("init-defaults", "/etc/default/traffic", context=deploy_context, use_sudo=True)
    sudo('chown root:root /etc/default/traffic')
    put('initscript', '/etc/init.d/traffic', use_sudo=True)
    sudo('chown root:root /etc/init.d/traffic')
    sudo('update-rc.d traffic defaults')
    sudo('chmod 755 /etc/init.d/traffic')
    sudo('/etc/init.d/traffic start', pty=False)
