# -*- coding: utf-8 -*-
"""
salt_utils.py

Description: Utility methods for configuration of Salt Cloud.
Written by:  maharg101 on 27th March 2018
"""

import io
import yaml


def generate_openstack_conf(params):
    """
    Generate an openstack.conf file-like given the supplied params dict.
    :param params: A dictionary containing parameters to use. See utils.populate_params.
    :return: StringIO populated with the generated openstack configuration.
    """
    openstack_conf_data = dict(
        openstack=dict(
            driver='openstack',
            region_name=params['OS_REGION_NAME'],
            auth=dict(
                username=params['OS_USERNAME'],
                password=params['OS_PASSWORD'],
                project_id=params['OS_PROJECT_ID'],
                auth_url=params['OS_AUTH_URL'],
                user_domain_name=params['OS_USER_DOMAIN_NAME'],
                project_domain_name=params['OS_PROJECT_DOMAIN_NAME'],
            ),
            networks=[
                dict(name='public', nat_source=True, routes_externally=True, routes_ipv4_externally=True),
                dict(name=params['network_name'], nat_destination=True, default_interface=True),
            ]
        )
    )
    openstack_conf = io.StringIO(yaml.dump(openstack_conf_data, default_flow_style=False))
    return openstack_conf
