# -*- coding: utf-8 -*-
"""
build_environment.py

Description: Build the environment as per the quick start using the OpenStack SDK
Written by:  maharg101 on 24th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import os
import pprint

from openstack import connection

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
    Main function. Call the various create methods in the correct order.

    Note that the methods display the created items on stdout, which is useful in a learning context.

    :return:
    """
    router = find_or_create_router(ROUTER_NAME)
    network = find_or_create_network(NETWORK_NAME)
    subnet = find_or_create_subnet(SUBNET_NAME, network=network)
    port = find_or_create_port(network, subnet)
    add_interface_to_router(router, subnet, port)
    _, public_ip_address = find_or_create_server('blog_app_1', network, subnet, port)
    print('server public ip address is %s' % public_ip_address)


def find_or_create_router(router_name):
    """
    Find or create the named router.

    Note:

    - This function *attempts* to ensure a singleton router based on the name, as this behaviour is somewhat
      useful in the context of iterating e.g. whilst learning the OpenStack SDK. You might not want this in
      a production context, as all sorts of race conditions could bite you if you weren't strict about managing
      router names, or didn't mind duplicate names for some other reason.

    - The 'public' network is assumed to exist. Again, this is for expediency in a learning scenario.

    :param router_name: The name of the router to find or create.
    :return: The found or created router
    """
    existing_router = conn.network.find_router(router_name)

    if existing_router:
        display('router %s found' % router_name, existing_router)
        return existing_router

    public_network = conn.network.find_network('public')
    router = conn.network.create_router(name=router_name, external_gateway_info=dict(network_id=public_network.id))
    display('router %s created' % router_name, router)
    return router


def find_or_create_network(network_name):
    """
    Find or create the named network.

    Note:

    - See the notes about find-or-create semantics on find_or_create_router()

    :param network_name: The name of the network to find or create.
    :return: The found or created network.
    """
    existing_network = conn.network.find_network(network_name)

    if existing_network:
        display('network %s found' % network_name, existing_network)
        return existing_network

    network = conn.network.create_network(name=network_name)
    display('network %s created' % network_name, network)
    return network


def find_or_create_subnet(subnet_name, network):
    """
    Find or create the named subnet.

    Note:

    - See the notes about find-or-create semantics on find_or_create_router()

    :param subnet_name: The name of the subnet to find or create.
    :param network: The related network.
    :return:
    """
    existing_subnet = conn.network.find_subnet(subnet_name)

    if existing_subnet:
        display('subnet %s found' % subnet_name, existing_subnet)
        return existing_subnet

    subnet = conn.network.create_subnet(
        name=subnet_name,
        cidr='10.0.0.0/24',
        ip_version=4,
        network_id=network.id,
        is_dhcp_enabled=True,
        dns_nameservers=['8.8.8.8'],
    )
    display('subnet %s created' % subnet_name, subnet)
    return subnet


def find_or_create_port(network, subnet):
    """
    Find or create a port on the given network / subnet
    Assumes existence of default security group. Hopefully that's safe in this context.

    Note:

    - See the notes about find-or-create semantics on find_or_create_router()

    :param network: The network to create the port on.
    :param subnet: The subnet which has the fixed IP address.
    :return: The Port
    """
    all_ports = conn.network.ports()

    # find ports on the correct network AND subnet
    ports_on_network_and_subnet = [
        port for port in all_ports if
        port.network_id == network.id and
        [
            fixed_ip for fixed_ip in port.fixed_ips if
            fixed_ip['subnet_id'] == subnet.id
        ]
    ]

    if ports_on_network_and_subnet:
        existing_port = ports_on_network_and_subnet[0]  # TODO - can there be more than one ?
        display('port %s found', existing_port)
        return existing_port

    default_security_group = conn.network.find_security_group('default')
    port = conn.network.create_port(network_id=network.id, security_groups=[str(default_security_group.id)])
    display('port created', port)
    return port


def add_interface_to_router(router, subnet, port):
    """
    Add an interface to the given router, for the specified subnet and port.
    :param router: The router to add the interface to.
    :param subnet: The subnet to use in the interface.
    :param port: The port to use in the interface.
    :return: The modified router
    """
    # Adding an interface for a given subnet and port is idempotent :)
    conn.network.add_interface_to_router(router, subnet_id=subnet.id, port_id=port.id)
    display('interface added to router', router)
    return router


def find_or_create_server(server_name, network, subnet, port, image_name='Ubuntu 16.04 LTS', flavor_name='m1.small'):
    """
    Create a server with the given details.

    Note:

    - See the notes about find-or-create semantics on find_or_create_router()

    - For compute there are several additional parameters which complicate things for find-or-create. This
      is a minimal viable approach to facilitate the learning process.

    - When the server is created, a floating IP address is reserved and attached to it.

    :param server_name: The name of the server
    :param network: The network to create the server on
    :param subnet: The subnet on which to create the floating IP address
    :param port: The port which the floating IP address will be attached to
    :param image_name: The name of the image to use - defaults to Ubuntu 16.04 LTS
    :param flavor_name: The name of the flavor to use - defaults to m1.small - m1.tiny is not recommended for Ubuntu
    :return: The server, and its public IP address
    """
    existing_server = conn.compute.find_server(server_name)

    if existing_server:
        display('server %s found' % server_name, existing_server)
        return existing_server

    image = conn.compute.find_image(image_name)
    flavor = conn.compute.find_flavor(flavor_name)

    params = dict(
        name=server_name,
        image_id=image.id,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
    )

    key_pairs = list(conn.compute.keypairs())
    if key_pairs:
        params['key_name'] = key_pairs[0].name

    server = conn.compute.create_server(**params)

    conn.compute.wait_for_server(server, status='ACTIVE')

    fixed_ip_address = server.addresses[network.name][0]['addr']

    public_network = conn.network.find_network('public')
    floating_ip = conn.network.create_ip(
        floating_network_id=public_network.id,
        port_id=port.id,
        subnet_id=subnet.id,
        fixed_ip_address=fixed_ip_address,
    )

    conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)

    display('server %s created' % server_name, server)
    return server, floating_ip.floating_ip_address


if __name__ == '__main__':
    main()
