# -*- coding: utf-8 -*-
"""
clear_environment.py

Description: Clear down the environment set up via quick start using the OpenStack SDK
Written by:  maharg101 on 24th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import sys
sys.path.insert(1, '..')  # adjust path to enable 'learning' utilities to remain isolated from core deliverables.

from openstack_infrastructure import facade as osf

# starter environment naming
SERVER_NAME = 'blog_app_1'
NETWORK_NAME = 'net1'
SUBNET_NAME = 'net1'
ROUTER_NAME = 'r1'


def main():
    """
    Main function. Call the various delete methods in the correct order.

    :return:
    """
    os_facade = osf.OpenStackFacade(silent=False)
    os_facade.delete_server(SERVER_NAME, NETWORK_NAME)
    os_facade.delete_subnet(SUBNET_NAME, ROUTER_NAME)
    os_facade.delete_network(NETWORK_NAME)
    os_facade.delete_router(ROUTER_NAME)


if __name__ == '__main__':
    main()
