# -*- coding: utf-8 -*-
"""
build_environment.py

Description: Build the environment as per the quick start using the OpenStack SDK
Written by:  maharg101 on 24th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import sys
sys.path.insert(1, '..')  # adjust path to enable 'learning' utilities to remain isolated from core deliverables.

from openstack_infrastructure import facade as osf  # noqa: E402

# starter environment naming
SERVER_NAME = 'blog_app_1'
NETWORK_NAME = 'net1'
SUBNET_NAME = 'net1'
ROUTER_NAME = 'r1'


def main():
    """
    Main function. Call the various find or create methods in the correct order.

    Note that the methods display the created items on stdout, which is useful in a learning context.

    :return:
    """
    os_facade = osf.OpenStackFacade(silent=False)
    router = os_facade.find_or_create_router(ROUTER_NAME)
    network = os_facade.find_or_create_network(NETWORK_NAME)
    subnet = os_facade.find_or_create_subnet(SUBNET_NAME, network=network)
    port = os_facade.find_or_create_port(network, subnet)
    os_facade.add_interface_to_router(router, subnet, port)
    server = os_facade.find_or_create_server(SERVER_NAME, network, subnet, port)
    public_ip_addresses = os_facade.get_public_addresses(server, NETWORK_NAME)
    if public_ip_addresses:
        print('server public ip address(es): %s' % ','.join([x.floating_ip_address for x in public_ip_addresses]))
    else:
        print('There seems to have been a problem obtaining a public IP address.')


if __name__ == '__main__':
    main()
