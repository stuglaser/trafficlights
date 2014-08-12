from fabric.api import *

env.use_ssh_config = True

def deploy():
    run('hostname')
