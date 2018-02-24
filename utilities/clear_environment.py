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

from openstack import connection, exceptions

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
    delete_server('blog_app_1')
    delete_security_group_rules_single_ip('default')

    delete_floating_ip(None)  # TODO - remove this faked call - see method for details...

    delete_subnet('net1', router_name='r1')
    delete_network('net1')
    delete_router('r1')


def delete_server(server_name):
    """
    Delete the server with the given name, if present.
    :param server_name: The name of the server to delete.
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

    delete_floating_ip(server)

    print('deleting server %s' % server_name)
    conn.compute.delete_server(server)


def delete_floating_ip(server):
    """
    Return floating IP addresses to the pool for the given server.
    :param server:  The server instance for which floating IP addresses are to be returned.
    :return:

    Screwed up first time around, and deleted server so will fake for now.
    Should have got the floating IP details from the following property of the server.
    addresses={
    'net1': [
    {'OS-EXT-IPS-MAC:mac_addr': '02:4c:fd:fc:4c:ef', 'version': 4,
    'addr': '10.0.0.3', 'OS-EXT-IPS:type': 'fixed'},
    {'OS-EXT-IPS-MAC:mac_addr': '02:4c:fd:fc:4c:ef', 'version': 4,
    'addr': '87.254.4.145', 'OS-EXT-IPS:type': 'floating'}]}
    """
    faked_floating_address_id = '2ebb8552-954f-4ba1-980f-e1b07b03f1b7'
    try:
        floating_ip = conn.network.get_ip(faked_floating_address_id)
    except exceptions.NotFoundException:
        print('could not find floating ip %s' % faked_floating_address_id)
        return

    display('floating IP address', floating_ip)

    print('deleting floating IP address %s' % floating_ip.floating_ip_address)
    conn.network.delete_ip(floating_ip)


def delete_security_group_rules_single_ip(security_group_name):
    """
    Delete rules from the named security group, where the remote_ip_prefix references a single IP i.e. /32
    :param security_group_name: The name of the security group from which to delete rules.
    :return:
    """
    all_rules = conn.network.security_group_rules(
        security_group_id=conn.network.find_security_group(security_group_name).id
    )

    # look at the remote_ip_prefix for each rule to see if it is a /32
    single_ip_rules = [
        x for x in all_rules if
        isinstance(x.remote_ip_prefix, str) and
        x.remote_ip_prefix.endswith('/32')  # TODO improve this - use a regex or something
    ]

    if not single_ip_rules:
        print('could not find any single IP rules in security group %s' % security_group_name)
        return

    display('single IP rules for security group %s' % security_group_name, single_ip_rules)

    print('deleting single IP rules for security group %s' % security_group_name)
    for single_ip_rule in single_ip_rules:
        conn.network.delete_security_group_rule(single_ip_rule)


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
