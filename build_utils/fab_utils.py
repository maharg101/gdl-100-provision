# -*- coding: utf-8 -*-
"""
fab_utils.py

Description: Fab utils for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

from fabric.api import *

env.user = 'ubuntu'
env.disable_known_hosts = True  # http://docs.fabfile.org/en/1.14/usage/ssh.html


def _bootstrap_salt_master():
    """
    Bootstrap the salt master
    :return:
    """
    code_dir = '/srv/salt'
    with settings(warn_only=True):
        if sudo("test -d %s" % code_dir).failed:
            print('git clone')
            sudo("git clone https://github.com/maharg101/gdl-100-salt %s" % code_dir)
    with settings(warn_only=False):
        with cd(code_dir):
            print('git pull')
            sudo("git pull")


def bootstrap_salt_master(salt_master_address):
    """
    Bootstrap the salt master.
    :param salt_master_address: The public address of the salt master
    :return: None
    """
    env.host_string = salt_master_address
    execute(_bootstrap_salt_master)
