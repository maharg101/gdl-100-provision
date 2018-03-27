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
        openstack_config=dict(
            identity_url='%s/auth/tokens' % params['OS_AUTH_URL'],
            auth_version=int(params['OS_IDENTITY_API_VERSION']),
            compute_name='nova',  # TODO - can this be different ?
            compute_region=params['OS_REGION_NAME'],
            service_type='compute',
            tenant=params['OS_USERNAME'],  # TODO - can the tenant be different from the username ?
            domain=params['OS_USER_DOMAIN_NAME'],  # TODO - should this be the user or project domain name ?
            user=params['OS_USERNAME'],
            password=params['OS_PASSWORD'],
            driver='openstack',
            ssh_key_name=params['key_name'],  # TODO - populate this earlier - currently done in facade.set_key_pair
            insecure=False,
            ssh_key_file='/etc/salt/pki/master/master.pem',
            networks=[
                dict(fixed=[params['fixed_network_id']]),  # TODO - populate this when known
                dict(floating=['public']),
            ]
        )
    )
    openstack_conf = io.StringIO(yaml.dump(openstack_conf_data, default_flow_style=False))
    return openstack_conf
