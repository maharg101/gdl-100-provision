# -*- coding: utf-8 -*-
"""
build.py

Description: Build the simple blog application.

build.py <app> <environment> <num_servers> <server_size>

Written by:  maharg101 on 25th February 2018
"""

import argparse
import logging
import os
import sys

from build_utils import fab_utils, salt_utils, utils
from collections import OrderedDict
from openstack_infrastructure import facade as osf

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

IMAGE_NAME = 'Ubuntu 16.04 LTS'
SALT_SERVER_PREFIX = 'salt'
APP_SERVER_PREFIX = 'app'


class InfrastructureManager(object):

    def __init__(self, params, os_facade):
        """
        Construct an InfrastructureBuilder
        :param params: A dictionary of params - see main() for details.
        :param os_facade: An instance of osf.OpenStackFacade
        """
        self.params = params
        self.os_facade = os_facade

    def prepare(self):
        """
        Prepare for the build / destroy steps.
        :return:
        """
        utils.populate_params_from_constructor_args(self.params)
        utils.populate_openstack_params_from_environ(self.params, os.environ)
        self.params['image_name'] = IMAGE_NAME
        self.validate_image_and_flavor()
        self.params['key_name'] = self.os_facade.get_name_of_first_key_pair()

    def build(self):
        """
        Perform the build steps in order.

        :return: OrderedDict containing 'server_name': [public_ip_addresses], String containing HA address
        """
        self.prepare()
        router = self.os_facade.find_or_create_router(self.params['router_name'])
        network = self.os_facade.find_or_create_network(self.params['network_name'])
        subnet = self.os_facade.find_or_create_subnet(self.params['subnet_name'], network=network)
        port = self.os_facade.find_or_create_port(network, subnet)
        self.os_facade.add_interface_to_router(router, subnet, port)
        servers = OrderedDict()
        salt_master_address = self.create_salt_server(network, port, subnet, servers)
        app_server_names = self.create_app_servers(network, port, subnet, servers, salt_master_address)
        fab_utils.accept_salt_minion_connections(salt_master_address, app_server_names)
        self.build_load_balancers(salt_master_address)
        ha_address = self.configure_keepalived(network, port, subnet, salt_master_address)
        fab_utils.apply_state(salt_master_address)
        return servers, ha_address

    def create_app_servers(self, network, port, subnet, servers, salt_master_address):
        """
        Create the app servers
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :param salt_master_address: The address of the salt master
        :return: A list of the server names
        """
        server_names = []
        for server_number in range(self.params['num_servers']):
            server_name_prefix = '%s-%s' % (APP_SERVER_PREFIX, server_number)
            public_ip_addresses = self.create_server(network, port, subnet, servers, server_name_prefix)
            if public_ip_addresses:
                fab_utils.bootstrap_salt_minion(public_ip_addresses[0].floating_ip_address, salt_master_address)
            else:
                logger.fatal('No public address found for salt minion for app server #%s' % server_number)
                sys.exit(1)
            server_names.append(utils.construct_server_name(self.params, server_name_prefix))
        return server_names

    def create_salt_server(self, network, port, subnet, servers):
        """
        Create the salt master server
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :return: The public IP address of the salt server
        """
        public_ip_addresses = self.create_server(network, port, subnet, servers, SALT_SERVER_PREFIX)
        if public_ip_addresses:
            salt_master_address = public_ip_addresses[0].floating_ip_address
            fab_utils.bootstrap_salt_master(salt_master_address)
            fab_utils.configure_salt_cloud(salt_master_address, salt_utils.generate_openstack_conf(self.params))
            self.configure_salt_cloud_key_pair(salt_master_address)
            return salt_master_address
        else:
            logger.fatal('No public address found for salt server')
            sys.exit(1)

    def configure_salt_cloud_key_pair(self, salt_master_address):
        """
        Configure the salt cloud key pair.
        The logic here is that the key is generated on first run, at which time openstack returns a key pair with
        a 'private_key' entry. This private key is then written as the root user private key on the salt master.
        On subsequent runs, the key is already in place. This works because openstack only returns the private key
        when the key pair is generated.
        :param salt_master_address: The address of the salt master server
        :return: None
        """
        key_pair = self.os_facade.get_or_create_key_pair('salt-cloud')
        private_key = getattr(key_pair, 'private_key', None)
        if private_key:
            logger.info('Writing private key for salt-cloud')
            fab_utils.write_salt_master_private_key(salt_master_address, private_key)
        else:
            logger.info('Private key for salt-cloud is already configured')

    def create_server(self, network, port, subnet, servers, server_name_prefix):
        """
        Create a server
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :param server_name_prefix: The prefix to be used in naming of the server
        :return: List of public IP addresses for the server
        """
        server_name = utils.construct_server_name(self.params, server_name_prefix)
        server = self.os_facade.find_or_create_server(server_name, network, subnet, port)
        public_ip_addresses = self.os_facade.get_public_addresses(server, self.params['network_name'])
        servers[server_name] = [x.floating_ip_address for x in public_ip_addresses]
        return public_ip_addresses

    def build_load_balancers(self, salt_master_address):
        """
        Build the load balancing instances using salt-cloud.
        :param salt_master_address: The address of the salt master server
        :return:
        """
        self.os_facade.get_or_create_vrrp_security_group()
        fab_utils.build_load_balancer_hosts(salt_master_address)

    def configure_keepalived(self, network, port, subnet, salt_master_address):
        """
        Configure highly available keepalived as described at https://github.com/100PercentIT/OpenStack-HA-Keepalived
        The two instances have been created with floating IP addresses assigned, we'll reuse the primary one.
        :param network: The network to which the server is connected
        :param port: The port to which all of the floating IP addresses are attached to
        :param subnet: The subnet on which the floating IP addresses are created
        :param salt_master_address: The address of the salt master server
        :return: String containing the highly available IP address
        """
        primary_server = self.os_facade.find_or_create_server('vrrp-primary', network, subnet, port)
        primary_server_port = next(self.os_facade.get_ports_for_server(primary_server), None)  # just one

        secondary_server = self.os_facade.find_or_create_server('vrrp-secondary', network, subnet, port)
        secondary_server_port = next(self.os_facade.get_ports_for_server(secondary_server), None)  # just one

        ha_floating_ip = self.get_ha_floating_ip_address(network, port, subnet, primary_server, secondary_server)

        fab_utils.place_ha_config_on_saltmaster(salt_master_address, primary_server_port, ha_floating_ip,
                                                secondary_server_port)
        return ha_floating_ip.floating_ip_address

    def get_ha_floating_ip_address(self, network, port, subnet, primary_server, secondary_server):
        """
        Get a floating IP address to use for high availability.

        The instances must have at least one floating IP at all times in order to be able to reach the openstack APIs.

        At run time there may be an existing HA floating IP assigned to either primary or secondary.
        Alternatively, on the first run, both servers will have only a single floating IP address.

        TODO - is there a way to route API requests that doesn't require a floating IP ?

        :param network: The network to which the servers are connected
        :param port: The port to which all of the floating IP addresses are attached to
        :param subnet: The subnet on which the floating IP addresses are created
        :param primary_server: The primary vrrp instance
        :param secondary_server: The secondary vrrp instance
        :return:
        """

        primary_addresses = self.os_facade.get_public_addresses(primary_server, self.params['network_name'])
        secondary_addresses = self.os_facade.get_public_addresses(secondary_server, self.params['network_name'])
        if len(primary_addresses) > 1:
            # re-use the second address which the primary server already has
            ha_floating_ip = primary_addresses[1]
        elif len(secondary_addresses) > 1:
            # re-use the second address which the secondary server already has
            ha_floating_ip = secondary_addresses[1]
        else:
            ha_floating_ip = self.os_facade.assign_floating_ip(network, port, primary_server, subnet)
        return ha_floating_ip

    def destroy(self):
        """
        Perform the destroy steps in order.
        :return:
        """
        self.prepare()
        self.delete_load_balancers()
        self.delete_app_servers()
        self.delete_salt_server()
        self.os_facade.delete_subnet(self.params['subnet_name'], self.params['router_name'])
        self.os_facade.delete_network(self.params['network_name'])
        self.os_facade.delete_router(self.params['router_name'])

    def delete_load_balancers(self):
        """
        Delete the load balancing servers and associated items.
        Note that salt-cloud is NOT used to destroy the instances themselves - it is simpler at this point to
        use the OpenStack SDK methods as exposed by facade.py. It is not obvious how the floating IP addresses are
        freed up when using salt-cloud.
        See destroy_load_balancer_hosts method in fab_utils for details of how it could work with salt-cloud.
        :return:
        """
        self.os_facade.delete_server('vrrp-primary', self.params['network_name'])
        self.os_facade.delete_server('vrrp-secondary', self.params['network_name'])
        self.os_facade.delete_key_pair('salt-cloud')
        self.os_facade.delete_security_group('vrrp')

    def delete_app_servers(self):
        """
        Delete the app servers
        :return: None
        """
        for server_number in range(self.params['num_servers']):
            server_name = utils.construct_server_name(self.params, '%s-%s' % (APP_SERVER_PREFIX, server_number))
            self.os_facade.delete_server(server_name, self.params['network_name'])

    def delete_salt_server(self):
        """
        Delete the salt master server
        :return: None
        """
        server_name = utils.construct_server_name(self.params, SALT_SERVER_PREFIX)
        self.os_facade.delete_server(server_name, self.params['network_name'])

    def validate_image_and_flavor(self):
        """
        Validate the selected image and flavor.
        :param params:
        :return:
        """
        image = self.os_facade.get_image(self.params['image_name'])
        if not image:
            logger.fatal('image %s does not exist.' % self.params['image_name'])
            sys.exit(1)

        flavor = self.os_facade.get_flavor(self.params['server_size'])
        if not flavor:
            logger.fatal('flavor %s does not exist.' % self.params['server_size'])
            sys.exit(1)

        validation_message = self.os_facade.validate_image_flavor_combination(image, flavor)
        if validation_message:
            logger.warning(validation_message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app", help="the name of the blog application e.g. hello_world")
    parser.add_argument("environment", help="the environment to build e.g. dev")
    parser.add_argument("num_servers", type=int, help="the number of application servers to build e.g. 1")
    parser.add_argument("server_size", help="the server size e.g. t1.micro")
    parser.add_argument("-d", "--destroy", help="destroy the environment, don't create it", action="store_true")
    args = parser.parse_args()
    manager = InfrastructureManager(vars(args), osf.OpenStackFacade(silent=False))
    if args.destroy:
        print('destroying...')
        manager.destroy()
    else:
        print('building...')
        servers, ha_address = manager.build()
        for server_name, public_ip_addresses in servers.items():
            print('server %s public IP address : %s' % (server_name, ','.join(public_ip_addresses)))
        print('blog is now available at %s' % ha_address)


if __name__ == '__main__':
    main()
