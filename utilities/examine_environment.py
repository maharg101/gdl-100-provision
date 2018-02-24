# -*- coding: utf-8 -*-
"""
examine_environment.py

Description: Examine the environment set up via quick start using the OpenStack SDK
Written by:  maharg101 on 24th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import os
import pprint

from openstack import connection

conn = connection.Connection(
    region_name=os.environ['OS_REGION_NAME'],
    auth=dict(
        auth_url=os.environ['OS_AUTH_URL'],
        username=os.environ['OS_USERNAME'],
        password=os.environ['OS_PASSWORD'],
        project_id=os.environ['OS_PROJECT_ID'],
        user_domain_id=os.environ['OS_USER_DOMAIN_NAME'],
    ),
    compute_api_version='2',
    identity_interface='internal',
)

pp = pprint.PrettyPrinter(indent=4)


def display(label, data):
    """
    Display a formatted label and data
    :param label: A short textual label for the data
    :param data: The data to be displayed. Typically a single, or list of objects.
    :return:
    """
    print(label)
    print('-' * len(label))
    pp.pprint(data)
    print()


def main():
    display('routers', list(conn.network.routers()))
    display('router r1', conn.network.find_router('r1'))
    display('networks', list(conn.network.networks()))
    display('network net1', conn.network.find_network("net1"))
    display('subnets', list(conn.network.subnets()))
    display('subnet net1', conn.network.find_subnet("net1"))
    display('security groups', list(conn.network.security_groups()))
    display('security group default', conn.network.find_security_group('default'))
    display(
        'security group rules',
        list(conn.network.security_group_rules(security_group_id=conn.network.find_security_group('default').id))
    )
    display('servers', list(conn.compute.servers()))
    display('server blog_app_1', conn.compute.get_server(conn.compute.find_server('blog_app_1')))
    display('flavors', list(conn.compute.flavors()))
    display('flavor m1.tiny', conn.compute.find_flavor('m1.tiny'))
    display('images', list(conn.compute.images()))
    display('image Ubuntu 16.04 LTS', conn.compute.find_image('Ubuntu 16.04 LTS'))


if __name__ == '__main__':
    main()
