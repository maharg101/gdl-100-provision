# -*- coding: utf-8 -*-
"""
utils.py

Description: Utility methods for build.py et al.
Written by:  maharg101 on 25th February 2018
"""

import re

ID_ALLOWED_PATTERN = re.compile('[^\w -]')  # we'll allow alphanumeric, underscore, dash, space


def populate_params(params):
    """
    Fully populate the params dict with values calculated from what was passed to the constructor.
    Note that the dict is updated in-place.
    :return: None
    """
    app_id = re.sub(ID_ALLOWED_PATTERN, '', params['app'])
    env_id = re.sub(ID_ALLOWED_PATTERN, '', params['environment'])
    params.update(
        dict(
            app=app_id,
            environment=env_id,
            router_name='router_%s_%s' % (app_id, env_id),
            network_name='network_%s_%s' % (app_id, env_id),
            subnet_name='subnet_%s_%s' % (app_id, env_id),
            server_base_name='server_%s_%s' % (app_id, env_id),
        )
    )


def construct_server_name(params, server_name_postfix):
    """
    Construct and return a server name for the given postfix
    :param server_name_postfix: An integer or string postfix to apply to the server base name
    :return: Server name string
    """
    return '%s_%s' % (params['server_base_name'], str(server_name_postfix))