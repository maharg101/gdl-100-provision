# -*- coding: utf-8 -*-
"""
fab_utils.py

Description: Fab utils for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

import functools
import io
import yaml

from fabric.api import *
from fabric.operations import put

env.connection_attempts = 5
env.disable_known_hosts = True  # http://docs.fabfile.org/en/1.14/usage/ssh.html
env.timeout = 30
env.user = 'ubuntu'


def _bootstrap_salt_master():
    """
    Bootstrap the salt master
    :return: None
    """
    salt_dir = '/srv'
    with settings(warn_only=True):
        with cd(salt_dir):
            if run('git rev-parse --git-dir > /dev/null 2>&1').failed:
                sudo('git clone https://github.com/maharg101/gdl-100-salt %s' % salt_dir)
    with settings(warn_only=False):
        with cd(salt_dir):
            sudo('git pull')
        with cd('/tmp'):
            run('curl -L https://bootstrap.saltstack.com -o install_salt.sh')
            sudo('sh install_salt.sh -M -L')
            sudo('apt-get  --yes --force-yes install python-pip')
            sudo('pip install shade')  # Salt Cloud 2018.3.0 requires shade but does not install it


def bootstrap_salt_master(salt_master_address):
    """
    Bootstrap the salt master.
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_master_address
    execute(_bootstrap_salt_master)


def _configure_salt_cloud(openstack_cloud_config):
    """
    Configure Salt Cloud on the salt master.
    :param openstack_cloud_config: The openstack cloud configuration (StringIO).
    :return: None
    """
    with cd('/etc/salt/cloud.providers.d/'):
        put(openstack_cloud_config, 'openstack.conf', use_sudo=True)
    with cd('/etc/salt/cloud.profiles.d/'):
        put(
            io.StringIO(
                yaml.dump(
                    dict(
                        m1_small_ubuntu=dict(
                            provider='openstack',
                            image='Ubuntu 16.04 LTS',
                            size='m1.small',
                            ssh_key_name='salt-cloud',
                            ssh_key_file='/root/.ssh/id_rsa',
                            ssh_username=env.user
                        )
                    ),
                    default_flow_style=False
                )
            ),
            'openstack.conf',
            use_sudo=True
        )
    with cd('/root/'):
        put(
            io.StringIO(
                yaml.dump(
                    {
                        'm1_small_ubuntu': {
                            'vrrp-primary': {'security_groups': ['default', 'vrrp']},
                            'vrrp-secondary': {'security_groups': ['default', 'vrrp']},
                            'vrrp-management': {'security_groups': ['default', 'vrrp']},
                        }
                    }
                )
            ),
            'vrrp-host-map',
            use_sudo=True
        )
    with cd('/etc/salt'):
        put(
            io.StringIO(
                yaml.dump(
                    {
                        'minion': {
                            'master': env.host_string  # this ensures that minions can find the master
                        }
                    }
                )
            ),
            'cloud',
            use_sudo=True
        )


def configure_salt_cloud(salt_master_address, openstack_cloud_config):
    """
    Configure Salt Cloud on the salt master.
    :param salt_master_address: The public address of the salt master
    :param openstack_cloud_config: The openstack cloud configuration (StringIO).
    :return: None
    """
    env.host_string = salt_master_address
    func = functools.partial(_configure_salt_cloud, openstack_cloud_config=openstack_cloud_config)
    execute(func)


def _bootstrap_salt_minion(salt_master_address):
    """
    Bootstrap a salt minion
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    with settings(warn_only=False):
        with cd('/tmp'):
            run('curl -L https://bootstrap.saltstack.com -o install_salt.sh')
            sudo('sh install_salt.sh -A %s' % salt_master_address)


def bootstrap_salt_minion(salt_minion_address, salt_master_address):
    """
    Bootstrap the salt master.
    :param salt_minion_address: The public address of the salt minion
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_minion_address
    func = functools.partial(_bootstrap_salt_minion, salt_master_address=salt_master_address)
    execute(func)


def _accept_salt_minion_connections(minion_connection_keys):
    """
    Accept salt minion connections.
    :param minion_connection_keys: A list of minion connection keys
    :return: None
    """
    with settings(warn_only=False):
        for minion_connection_key in minion_connection_keys:
            sudo('salt-key --accept=%s --yes' % minion_connection_key)


def accept_salt_minion_connections(salt_master_address, minion_connection_keys):
    """
    Accept salt minion connections.
    :param salt_master_address: The public address of the salt master
    :param minion_connection_keys: A list of minion connection names
    :return: None
    """
    env.host_string = salt_master_address
    func = functools.partial(_accept_salt_minion_connections, minion_connection_keys=minion_connection_keys)
    execute(func)


def _write_salt_master_private_key(private_key):
    """
    Write the private key for the root user on the the salt master.
    :param private_key: The private key to write.
    :return: None
    """
    with cd('/root/.ssh'):
        put(io.StringIO(private_key), 'id_rsa', mode=0o0600, use_sudo=True)
        sudo('chown root. id_rsa')


def write_salt_master_private_key(salt_master_address, private_key):
    """
    Write the private key for the root user on the the salt master.
    :param salt_master_address: The public address of the salt master
    :param private_key: The private key to write.
    :return: None
    """
    env.host_string = salt_master_address
    func = functools.partial(_write_salt_master_private_key, private_key=private_key)
    execute(func)


def _apply_state():
    """
    Apply the salt state.
    :return: None
    """
    with settings(warn_only=False):
        sudo('sh /srv/apply_state.sh')


def apply_state(salt_master_address):
    """
    Apply the salt state.
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_master_address
    execute(_apply_state)


def _build_load_balancer_hosts():
    """
    Invoke salt-cloud to build the load balancer hosts.
    :return: None
    """
    # -P can be used to run in parallel - but can cause timeouts - see https://github.com/saltstack/salt/issues/46663
    # -y assumes yes
    sudo('salt-cloud -m /root/vrrp-host-map -y --out=highstate --state-output=terse')


def build_load_balancer_hosts(salt_master_address):
    """
    Invoke salt-cloud to build the load balancer hosts.
    :param salt_master_address:
    :return: None
    """
    env.host_string = salt_master_address
    execute(_build_load_balancer_hosts)


def _destroy_load_balancer_hosts():
    """
    Invoke salt-cloud to destroy the load balancer hosts.
    N.B.
     - In practice this project uses the OpenStack SDK via facade.py in preference to this method.
     - See delete_load_balancers method in build.py
    :return: None
    """
    sudo('salt-cloud -m /root/vrrp-host-map -d -y')


def destroy_load_balancer_hosts(salt_master_address):
    """
    Invoke salt-cloud to destroy the load balancer hosts.
    N.B.
     - In practice this project uses the OpenStack SDK via facade.py in preference to this method.
     - See delete_load_balancers method in build.py
    :param salt_master_address:
    :return: None
    """
    env.host_string = salt_master_address
    execute(_destroy_load_balancer_hosts)
