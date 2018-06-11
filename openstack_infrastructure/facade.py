# -*- coding: utf-8 -*-
"""
facade.py

Description: OpenStack SDK operations wrapped in convenience methods.
Written by:  maharg101 on 25th February 2018

Related links:
 - https://docs.openstack.org/python-openstacksdk/latest/user/
"""

import os
import ipaddress
import pprint
import time

from openstack import connection, exceptions

pp = pprint.PrettyPrinter(indent=4)


class OpenStackFacade(object):

    def __init__(self, conn=None, silent=True):
        """
        Construct an OpenStackFacade.

        :param conn: An optional OpenStack SDK connection.Connection object. Connection details are taken from the
                     environment if conn is not supplied.
        :param silent: Output will be displayed if set to False. Defaults to True.
        """
        if not conn:
            self.conn = self.create_connection_from_environ()
        else:
            self.conn = conn
        if silent:
            self.silent_mode()

    # --------------------- Connection methods ---------------------

    @staticmethod
    def create_connection_from_environ():
        """
        Create an OpenStack connection.Connection based on the environment.
        :param self:
        :return:
        """
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
        return conn

    # --------------------- Display methods ---------------------

    @staticmethod
    def silent_mode():
        """
        Run in silent mode.
        :return:
        """
        __class__.display = lambda *args, **kwargs: None

    @staticmethod
    def display(label, data=None):
        """
        Display a label and, optionally, some data
        :param label: A short textual label for the data
        :param data: The data to be displayed. Typically a single, or list of objects. Optional.
        :return:
        """
        print()
        print(label)
        if data:
            print('-' * len(label))
            pp.pprint(data)
        print()

    # --------------------- Build methods ---------------------

    def find_or_create_router(self, router_name):
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
        existing_router = self.conn.network.find_router(router_name)
    
        if existing_router:
            self.display('router %s found' % router_name, existing_router)
            return existing_router
    
        public_network = self.conn.network.find_network('public')
        router = self.conn.network.create_router(
            name=router_name, external_gateway_info=dict(network_id=public_network.id)
        )
        self.display('router %s created' % router_name, router)
        return router
    
    def find_or_create_network(self, network_name):
        """
        Find or create the named network.
    
        Note:
    
        - See the notes about find-or-create semantics on find_or_create_router()
    
        :param network_name: The name of the network to find or create.
        :return: The found or created network.
        """
        existing_network = self.conn.network.find_network(network_name)
    
        if existing_network:
            self.display('network %s found' % network_name, existing_network)
            return existing_network
    
        network = self.conn.network.create_network(name=network_name)
        self.display('network %s created' % network_name, network)
        return network

    def find_or_create_subnet(self, subnet_name, network):
        """
        Find or create the named subnet.
    
        Note:
    
        - See the notes about find-or-create semantics on find_or_create_router()
    
        :param subnet_name: The name of the subnet to find or create.
        :param network: The related network.
        :return:
        """
        existing_subnet = self.conn.network.find_subnet(subnet_name)
    
        if existing_subnet:
            self.display('subnet %s found' % subnet_name, existing_subnet)
            return existing_subnet
    
        subnet = self.conn.network.create_subnet(
            name=subnet_name,
            cidr='10.0.0.0/24',
            ip_version=4,
            network_id=network.id,
            is_dhcp_enabled=True,
            dns_nameservers=['8.8.8.8'],
        )
        self.display('subnet %s created' % subnet_name, subnet)
        return subnet

    def find_or_create_port(self, network, subnet):
        """
        Find or create a port on the given network / subnet
        Assumes existence of default security group. Hopefully that's safe in this context.
    
        Note:
    
        - See the notes about find-or-create semantics on find_or_create_router()
    
        :param network: The network to create the port on.
        :param subnet: The subnet which has the fixed IP address.
        :return: The Port
        """
        all_ports = self.conn.network.ports()
    
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
            self.display('port found', existing_port)
            return existing_port
    
        default_security_group = self.conn.network.find_security_group('default')
        port = self.conn.network.create_port(network_id=network.id, security_groups=[str(default_security_group.id)])
        self.display('port created', port)
        return port

    def add_interface_to_router(self, router, subnet, port):
        """
        Add an interface to the given router, for the specified subnet and port.
        :param router: The router to add the interface to.
        :param subnet: The subnet to use in the interface.
        :param port: The port to use in the interface.
        :return: The modified router
        """
        # Adding an interface for a given subnet and port is idempotent :)
        self.conn.network.add_interface_to_router(router, subnet_id=subnet.id, port_id=port.id)
        self.display('interface added to router', router)
        return router

    def find_or_create_server(self, server_name, network, subnet, port,
                              image_name='Ubuntu 16.04 LTS', flavor_name='m1.small'):
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
        :param flavor_name: The name of the flavor to use. Defaults to m1.small.
        :return: The server, and its public IP address
        """
        pre_existing_server = self.conn.compute.find_server(server_name)
    
        if pre_existing_server:
            server = self.conn.compute.get_server(pre_existing_server.id)
            self.display('server %s found' % server_name, server)
            return server

        image = self.get_image(image_name)
        flavor = self.get_flavor(flavor_name)
    
        server_params = dict(
            name=server_name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[{"uuid": network.id}],
        )
        self.set_key_pair_name(server_params)
        server = self.conn.compute.create_server(**server_params)
        self.conn.compute.wait_for_server(server, status='ACTIVE', wait=300)
        self.assign_floating_ip(network, port, server, subnet)
        created_server = self.conn.compute.get_server(server.id)
        self.display('server %s created' % server_name, created_server)
        return created_server

    def assign_floating_ip(self, network, port, server, subnet):
        """
        Assign a floating IP address to the server.
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param server: The server which the floating IP will be assigned to
        :param subnet: The subnet on which to create the floating IP address

        :return: The floating IP object
        """
        fixed_ip_address = server.addresses[network.name][0]['addr']
        public_network = self.conn.network.find_network('public')
        floating_ip = self.conn.network.create_ip(
            floating_network_id=public_network.id,
            port_id=port.id,
            subnet_id=subnet.id,
            fixed_ip_address=fixed_ip_address,
        )
        self.conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
        return floating_ip

    def get_name_of_first_key_pair(self):
        """
        Return the name of the first key pair found, or None.
        :return: The name of the first key pair found, or None.
        """
        key_pairs = list(self.conn.compute.keypairs())
        if key_pairs:
            return key_pairs[0].name

    def set_key_pair_name(self, server_params):
        """
        Add the name of the first key pair found (if any) to the params for the server.
        :param server_params: The server params dict to add the key pair to.
        :return:
        """
        key_name = self.get_name_of_first_key_pair()
        if key_name:
            server_params['key_name'] = key_name

    def get_or_create_key_pair(self, name):
        """
        Get or create a key pair with the given name.
        :param name: The name of the key pair
        :return: The key pair.
        """
        key_pair = self.conn.compute.find_keypair(name)
        if not key_pair:
            key_pair = self.conn.compute.create_keypair(name=name)
            self.display('created new key pair %s' % key_pair)
        else:
            self.display('got existing key pair %s' % key_pair)
        return key_pair

    def get_or_create_vrrp_security_group(self):
        """
        Get or create the vrrp security group.
        :return: The vrrp security group object.
        """
        vrrp_group = self.conn.network.find_security_group('vrrp')
        if not vrrp_group:
            vrrp_group = self.conn.network.create_security_group(name='vrrp', description='vrrp')
            self.display('created new security group', vrrp_group)
            vrrp_rule = self.conn.network.create_security_group_rule(
                security_group_id=vrrp_group.id,
                protocol=112,
                direction='ingress'
            )
            self.display('created new security group rule', vrrp_rule)
        else:
            self.display('got existing security group', vrrp_group)
        return vrrp_group

    # --------------------- Destroy methods ---------------------

    def delete_server(self, server_name, network_name):
        """
        Delete the server with the given name, if present.
        :param server_name: The name of the server to delete.
        :param network_name: The name of the network to which the server is attached.
        :return:
        """
        try:
            server = self.conn.compute.get_server(self.conn.compute.find_server(server_name))
        except exceptions.InvalidRequest:
            self.display('could not find server %s' % server_name)
            return

        self.display('server %s' % server_name, server)

        if server.status == 'ACTIVE':
            self.display('stopping server....')
            self.conn.compute.stop_server(server)
            self.conn.compute.wait_for_server(server, status='SHUTOFF')
            self.display('server has stopped')

        self.delete_floating_ip(server, network_name)

        self.display('deleting server %s' % server_name)
        self.conn.compute.delete_server(server, force=True)  # be on the safe side..
        self.wait_for_server_to_vanish(server_name)

    def wait_for_server_to_vanish(self, server_name, attempts=10, sleep_seconds=10):
        """
        Wait for a recently deleted server to actually go.
        There can be a delay between the delete instruction, and the actual removal of the server from OpenStack.
        Note that wait_for_server doesn't really work for this use case.
        :param server_name: The name of the delete to inspect.
        :param attempts: The number of attempts to make before giving up.
        :param sleep_seconds: The number of seconds to sleep between attempts.
        :return: None
        """
        for attempt in range(1, attempts+1):
            self.display('waiting for server %s to vanish, attempt %s of %s' % (server_name, attempt, attempts))
            try:
                server = self.conn.compute.find_server(server_name)
                if server:
                    self.display('found server %s' % server_name, server)
                    time.sleep(sleep_seconds)
                else:
                    self.display('could not find server %s' % server_name)
                    return
            except exceptions.InvalidRequest:
                self.display('could not find server %s' % server_name)
                return
        self.display('giving up - server %s may still be present...' % server_name)

    def delete_floating_ip(self, server, network_name):
        """
        Release floating IP addresses to the pool for the given server.
        :param server:  The server instance for which floating IP addresses are to be released.
        :param network_name: The name of the network to which the server is attached.
        :return:
        """

        floating_ips_for_this_server = self.get_public_addresses(server, network_name)

        self.display('floating IP address(es)', floating_ips_for_this_server or 'None found')

        if floating_ips_for_this_server:
            for floating_ip in floating_ips_for_this_server:
                self.display('deleting floating IP address %s' % floating_ip.floating_ip_address)
                self.conn.network.delete_ip(floating_ip)

    def delete_subnet(self, subnet_name, router_name):
        """
        Delete the named subnet.
        In order to delete the subnet, it is necessary to first call delete_ports()
        :param subnet_name: The name of the subnet to delete.
        :param router_name: The name of the related router.
        :return:
        """
        subnet = self.conn.network.find_subnet(subnet_name)

        if not subnet:
            self.display('could not find subnet %s' % subnet_name)
            return

        self.display('subnet %s' % subnet_name, subnet)

        router = self.conn.network.find_router(router_name)

        if not router:
            self.display('could not find router %s' % router_name)
            return

        self.delete_ports(subnet, router)

        self.display('deleting subnet %s' % subnet_name)
        self.conn.network.delete_subnet(subnet)

    def delete_ports(self, subnet, router):
        """
        Delete port(s) for a given subnet and router.
        Note that in order to delete ports, it is necessary to first delete the related interfaces from the router.
        :param subnet: The subnet for which the port is to be deleted.
        :param router: The router to which the port(s) and subnet are attached.
        :return:
        """
        all_ports = self.conn.network.ports()

        # each port can have multiple fixed_ips, so need to look inside each one to examine the subnet
        ports_on_required_subnet = [
            port for port in all_ports if
            [
                fixed_ip for fixed_ip in port.fixed_ips if
                fixed_ip['subnet_id'] == subnet.id
            ]
        ]

        if not ports_on_required_subnet:
            self.display('could not find any ports in the subnet %s' % subnet.name)
            return

        self.display('ports on subnet %s' % subnet.name, ports_on_required_subnet)

        self.display('deleting ports on subnet %s' % subnet.name)
        for port in ports_on_required_subnet:
            self.conn.network.remove_interface_from_router(router, subnet.id, port.id)
            self.conn.network.delete_port(port)

    def delete_network(self, network_name):
        """
        Delete the named network.
        :param network_name: The name of the network to delete.
        :return:
        """
        network = self.conn.network.find_network(network_name)

        if not network:
            self.display('could not find network %s' % network_name)
            return

        self.display('network %s' % network_name, network)

        self.display('deleting network %s' % network_name)
        self.conn.network.delete_network(network)

    def delete_router(self, router_name):
        """
        Delete the named router.
        :param router_name: The name of the router to delete.
        :return:
        """
        router = self.conn.network.find_router(router_name)

        if not router:
            self.display('could not find router %s' % router_name)
            return

        self.display('router %s' % router_name, router)

        self.display('deleting router %s' % router_name)
        self.conn.network.delete_router(router)

    def delete_security_group(self, name):
        """
        Delete a security group.
        :param name: The name of the security group to delete.
        :return: None
        """
        group = self.conn.network.find_security_group(name)
        if not group:
            self.display('could not find security group %s' % name)
            return

        self.display('security group %s' % name, group)

        self.display('deleting security group %s' % name)
        self.conn.network.delete_security_group(group)

    def delete_key_pair(self, name):
        """
        Delete a key pair with the given name.
        :param name: The name of the key pair
        :return: None
        """
        key_pair = self.conn.compute.find_keypair(name)
        if not key_pair:
            self.display('could not find key pair %s' % key_pair)
        else:
            self.display('deleting key pair %s' % key_pair)
            self.conn.compute.delete_keypair(name)

    # --------------------- Utility methods ---------------------

    def get_public_addresses(self, server, network_name):
        """
        Return a list of public (floating IP) addresses for the given server on the named network.
        :param server: The server for which to return the addresses.
        :param network_name: The name of the network which the addresses are associated with.
        :return: A list of floating IP objects, or None if none are present.
        """
        try:
            fixed_address = server.addresses[network_name][0]['addr']
        except KeyError:
            floating_ips_for_this_server = None
        except TypeError:
            floating_ips_for_this_server = None
        else:
            assert ipaddress.IPv4Address(fixed_address).is_private  # TODO - handle this properly
            floating_ips = list(
                self.conn.network.ips()  # querying with fixed_ip_address=fixed_address seems to be broken ? .....
            )
            floating_ips_for_this_server = [x for x in floating_ips if x.fixed_ip_address == fixed_address]
        return floating_ips_for_this_server

    def get_flavor(self, flavor_name):
        """
        Get a flavor object by name.
        :param flavor_name: The name of the flavor to get.
        :return: The Flavor object.
        """
        flavor_stub = self.conn.compute.find_flavor(flavor_name)
        if flavor_stub:
            return self.conn.compute.get_flavor(flavor_stub.id)

    def get_image(self, image_name):
        """
        Get an image object by name.
        :param image_name: The name of the image to get.
        :return: The Image object.
        """
        image_stub = self.conn.compute.find_image(image_name)
        if image_stub:
            return self.conn.compute.get_image(image_stub.id)

    @staticmethod
    def validate_image_flavor_combination(image, flavor):
        """
        Validate a combination of image and flavor.
        :param image_name: The image.
        :param flavor_name: The flavor.
        :return: None if the combination is valid, or a string containing an explanatory message if invalid.
        """
        ram_woe = flavor.ram < image.min_ram
        disk_woe = flavor.disk < image.min_disk

        if ram_woe and disk_woe:
            message = '%s does not have the minimum recommended RAM or disk for %s' % (flavor.name, image.name)
        elif ram_woe:
            message = '%s does not have the minimum recommended RAM for %s' % (flavor.name, image.name)
        elif disk_woe:
            message = '%s does not have the minimum recommended disk for %s' % (flavor.name, image.name)
        else:
            message = None

        return message

