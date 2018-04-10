# -*- coding: utf-8 -*-
"""
utils.py

Description: Utility methods for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

import os
import re

ID_ALLOWED_PATTERN = re.compile('[^\w -]')  # we'll allow alphanumeric, underscore, dash, space
TO_DASH_PATTERN = re.compile('[ _]')  # spaces and underscores are replaced with dashes


def populate_params_from_constructor_args(params):
    """
    Fully populate the params dict with values calculated from what was passed to the constructor.
    Note that:
     - The dict is updated in-place.
     - The app_id and env_id naming elements are stripped of characters matching the ID_ALLOWED_PATTERN.
     - Spaces and underscores are replaced with dashes.
    :param params: The params dict to populate
    :return: None
    """
    app_id = re.sub(TO_DASH_PATTERN, '-', re.sub(ID_ALLOWED_PATTERN, '', params['app']))
    env_id = re.sub(TO_DASH_PATTERN, '-', re.sub(ID_ALLOWED_PATTERN, '', params['environment']))
    params.update(
        dict(
            app=app_id,
            environment=env_id,
            router_name='router-%s-%s' % (app_id, env_id),
            network_name='network-%s-%s' % (app_id, env_id),
            subnet_name='subnet-%s-%s' % (app_id, env_id),
            server_base_name='%s-%s' % (app_id, env_id),
        )
    )


def populate_openstack_params_from_environ(params, env_dict):
    """
    Populate the params dict with Openstack variables from supplied environment dict.
    Note that:
     - The dict is updated in-place.
    :param params: The params dict to populate
    :param env_dict: The environment dict which contains the Openstack variables.
    :return:
    """
    params.update(
        {
            k: v
            for k, v in env_dict.items()
            if k in [
                'OS_AUTH_URL',
                'OS_IDENTITY_API_VERSION',
                'OS_REGION_NAME',
                'OS_USERNAME',
                'OS_PROJECT_DOMAIN_NAME',
                'OS_USER_DOMAIN_NAME',
                'OS_PASSWORD',
                'OS_PROJECT_ID',
            ]
        }
    )


def construct_server_name(params, server_name_prefix):
    """
    Construct and return a server name for the given prefix
    :param params: The params dict containing the server base name
    :param server_name_prefix: A string prefix to apply to the server base name
    :return: Server name string
    """
    return '%s-%s' % (str(server_name_prefix), params['server_base_name'])