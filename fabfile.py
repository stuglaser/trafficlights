from fabric.api import *
from fabric.contrib import files

env.use_ssh_config = True

def setup_nanomsg():
    RELEASE = 'nanomsg-0.4-beta'
    TARBALL = '%s.tar.gz' % RELEASE
    if not files.exists(TARBALL):
        run('wget http://download.nanomsg.org/%s' % TARBALL)
    run('tar xf %s' % TARBALL)
    with cd(RELEASE):
        run('./configure')
        run('make')
        sudo('make install')
    sudo('ldconfig')


def setup_nanomsg_python():
    REPO_NAME = 'nanomsg-python'
    HASH = '742d39a520230da373552fd0f1858feefc623b15'
    REPO_URL = 'https://github.com/tonysimpson/nanomsg-python.git'
    if not files.exists(REPO_NAME):
        run('git clone %s' % REPO_URL)
    with cd(REPO_NAME):
        run('git checkout %s' % HASH)
        sudo('python setup.py install')


def setup():
    setup_nanomsg()
    setup_nanomsg_python()
    sudo('pip install chan')


def deploy():
    run('hostname')
    put('traffic.py')
    put('lights.py')
    put('init-%s' % env.host_string, '/etc/init.d/traffic', use_sudo=True)
    sudo('chown root:root /etc/init.d/traffic')
    sudo('chmod 755 /etc/init.d/traffic')
