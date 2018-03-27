# -*- coding: utf-8 -*-
"""
fab_utils.py

Description: Fab utils for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

import functools

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


def configure_salt_cloud(salt_master_address, openstack_cloud_config):
    """
    Configure Salt Cloud on the salt master.
    :param salt_master_address: The public address of the salt master
    :param openstack_cloud_config: The openstack cloud configuration (StringIO).
    :return:
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