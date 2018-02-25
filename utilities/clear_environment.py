# -*- coding: utf-8 -*-
"""
clear_environment.py

Description: Clear down the environment set up via quick start using the OpenStack SDK
Written by:  maharg101 on 24th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import os
import pprint
import ipaddress

from openstack import connection, exceptions

# starter environment naming
SERVER_NAME = 'blog_app_1'
NETWORK_NAME = 'net1'
SUBNET_NAME = 'net1'
ROUTER_NAME = 'r1'

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
    print()
    print(label)
    print('-' * len(label))
    pp.pprint(data)
    print()


def main():
    """
    Main function. Call the various delete methods in the correct order.
    :return:
    """
    delete_server(SERVER_NAME, NETWORK_NAME)
    delete_subnet(SUBNET_NAME, ROUTER_NAME)
    delete_network(NETWORK_NAME)
    delete_router(ROUTER_NAME)


def delete_server(server_name, network_name):
    """
    Delete the server with the given name, if present.
    :param server_name: The name of the server to delete.
    :param network_name: The name of the network to which the server is attached.
    :return:
    """
    try:
        server = conn.compute.get_server(conn.compute.find_server(server_name))
    except exceptions.InvalidRequest:
        print('could not find server %s' % server_name)
        return

    display('server %s' % server_name, server)

    if server.status == 'ACTIVE':
        print('stopping server....')
        conn.compute.stop_server(server)
        conn.compute.wait_for_server(server, status='SHUTOFF')
        print('server has stopped')

    delete_floating_ip(server, network_name)

    print('deleting server %s' % server_name)
    conn.compute.delete_server(server)


def delete_floating_ip(server, network_name):
    """
    Release floating IP addresses to the pool for the given server.
    :param server:  The server instance for which floating IP addresses are to be released.
    :param network_name: The name of the network to which the server is attached.
    :return:
    """
    try:
        fixed_address = server.addresses[network_name][0]['addr']
    except KeyError:
        print('no floating IP found')
        return

    assert ipaddress.IPv4Address(fixed_address).is_private  # TODO - handle this properly

    floating_ips = list(conn.network.ips())  # querying with fixed_ip_address=fixed_address seems to be broken ? .....
    floating_ips_to_delete = [x for x in floating_ips if x.fixed_ip_address == fixed_address]

    display('floating IP address(es)', floating_ips_to_delete)

    for floating_ip in floating_ips_to_delete:
        print('deleting floating IP address %s' % floating_ip.floating_ip_address)
        conn.network.delete_ip(floating_ip)


def delete_subnet(subnet_name, router_name):
    """
    Delete the named subnet.
    In order to delete the subnet, it is necessary to first call delete_ports()
    :param subnet_name: The name of the subnet to delete.
    :param router_name: The name of the related router.
    :return:
    """
    subnet = conn.network.find_subnet(subnet_name)

    if not subnet:
        print('could not find subnet %s' % subnet_name)
        return

    display('subnet %s' % subnet_name, subnet)

    router = conn.network.find_router(router_name)

    if not router:
        print('could not find router %s' % router_name)
        return

    delete_ports(subnet, router)

    print('deleting subnet %s' % subnet_name)
    conn.network.delete_subnet(subnet)


def delete_ports(subnet, router):
    """
    Delete port(s) for a given subnet and router.
    Note that in order to delete ports, it is necessary to first delete the related interfaces from the router.
    :param subnet: The subnet for which the port is to be deleted.
    :param router: The router to which the port(s) and subnet are attached.
    :return:
    """
    all_ports = conn.network.ports()

    # each port can have multiple fixed_ips, so need to look inside each one to examine the subnet
    ports_on_required_subnet = [
        port for port in all_ports if
        [
            fixed_ip for fixed_ip in port.fixed_ips if
            fixed_ip['subnet_id'] == subnet.id
        ]
    ]

    if not ports_on_required_subnet:
        print('could not find any ports in the subnet %s' % subnet.name)
        return

    display('ports on subnet %s' % subnet.name, ports_on_required_subnet)

    print('deleting ports on subnet %s' % subnet.name)
    for port in ports_on_required_subnet:
        conn.network.remove_interface_from_router(router, subnet.id, port.id)
        conn.network.delete_port(port)


def delete_network(network_name):
    """
    Delete the named network.
    :param network_name: The name of the network to delete.
    :return:
    """
    network = conn.network.find_network(network_name)

    if not network:
        print('could not find network %s' % network_name)
        return

    display('network %s' % network_name, network)

    print('deleting network %s' % network_name)
    conn.network.delete_network(network)


def delete_router(router_name):
    """
    Delete the named router.
    :param router_name: The name of the router to delete.
    :return:
    """
    router = conn.network.find_router(router_name)

    if not router:
        print('could not find router %s' % router_name)
        return

    display('router %s' % router_name, router)

    print('deleting router %s' % router_name)
    conn.network.delete_router(router)


if __name__ == '__main__':
    main()
