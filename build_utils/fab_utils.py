# -*- coding: utf-8 -*-
"""
fab_utils.py

Description: Fab utils for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

import functools

from fabric.api import *

env.connection_attempts = 5
env.disable_known_hosts = True  # http://docs.fabfile.org/en/1.14/usage/ssh.html
env.timeout = 30
env.user = 'ubuntu'


def _bootstrap_salt_master():
    """
    Bootstrap the salt master
    :return: None
    """
    salt_dir = '/srv/salt'
    with settings(warn_only=True):
        if sudo('test -d %s' % salt_dir).failed:
            sudo('git clone https://github.com/maharg101/gdl-100-salt %s' % salt_dir)
    with settings(warn_only=False):
        with cd(salt_dir):
            sudo('git pull')
        with cd('/tmp'):
            run('curl -L https://bootstrap.saltstack.com -o install_salt.sh')
            sudo('sh install_salt.sh -M')


def bootstrap_salt_master(salt_master_address):
    """
    Bootstrap the salt master.
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_master_address
    execute(_bootstrap_salt_master)


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
        sudo('sh /srv/salt/apply_state.sh')


def apply_state(salt_master_address):
    """
    Apply the salt state.
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_master_address
    execute(_apply_state)