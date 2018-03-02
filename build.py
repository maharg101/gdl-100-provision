# -*- coding: utf-8 -*-
"""
build.py

Description: Build the simple blog application.

build.py <app> <environment> <num_servers> <server_size>

Written by:  maharg101 on 25th February 2018
"""

import argparse
import logging
import sys

from build_utils import utils
from collections import OrderedDict
from openstack_infrastructure import facade as osf

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

IMAGE_NAME = 'Ubuntu 16.04 LTS'
SALT_SERVER_POSTFIX = 'salt'


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
        utils.populate_params(self.params)
        self.params['image_name'] = IMAGE_NAME
        self.validate_image_and_flavor()

    def build(self):
        """
        Perform the build steps in order.

        :return: OrderedDict containing 'server_name': [public_ip_addresses]
        """
        self.prepare()
        router = self.os_facade.find_or_create_router(self.params['router_name'])
        network = self.os_facade.find_or_create_network(self.params['network_name'])
        subnet = self.os_facade.find_or_create_subnet(self.params['subnet_name'], network=network)
        port = self.os_facade.find_or_create_port(network, subnet)
        self.os_facade.add_interface_to_router(router, subnet, port)
        servers = OrderedDict()
        self.create_salt_server(network, port, subnet, servers)
        self.create_app_servers(network, port, subnet, servers)
        return servers

    def create_app_servers(self, network, port, subnet, servers):
        """
        Create the app servers
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :return: None
        """
        for server_number in range(self.params['num_servers']):
            self.create_server(network, port, subnet, servers, server_number)

    def create_salt_server(self, network, port, subnet, servers):
        """
        Create the salt master server
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :return: None
        """
        self.create_server(network, port, subnet, servers, SALT_SERVER_POSTFIX)

    def create_server(self, network, port, subnet, servers, server_name):
        """
        Create a server
        :param network: The network to create the server on
        :param port: The port which the floating IP address will be attached to
        :param subnet: The subnet on which to create the floating IP address
        :param servers: A dict to add the server name and IP address(es) to
        :param server_name: The name of the server
        :return: None
        """
        server_name = utils.construct_server_name(self.params, server_name)
        server = self.os_facade.find_or_create_server(server_name, network, subnet, port)
        public_ip_addresses = self.os_facade.get_public_addresses(server, self.params['network_name'])
        servers[server_name] = [x.floating_ip_address for x in public_ip_addresses]

    def destroy(self):
        """
        Perform the destroy steps in order.

        :return:
        """
        self.prepare()
        self.delete_app_servers()
        self.delete_salt_server()
        self.os_facade.delete_subnet(self.params['subnet_name'], self.params['router_name'])
        self.os_facade.delete_network(self.params['network_name'])
        self.os_facade.delete_router(self.params['router_name'])

    def delete_app_servers(self):
        """
        Delete the app servers
        :return: None
        """
        for server_number in range(self.params['num_servers']):
            server_name = utils.construct_server_name(self.params, server_number)
            self.os_facade.delete_server(server_name, self.params['network_name'])

    def delete_salt_server(self):
        """
        Delete the salt master server
        :return: None
        """
        server_name = utils.construct_server_name(self.params, SALT_SERVER_POSTFIX)
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
    builder = InfrastructureManager(vars(args), osf.OpenStackFacade(silent=False))
    if args.destroy:
        print('destroying...')
        builder.destroy()
    else:
        print('building...')
        servers = builder.build()
        for server_name, public_ip_addresses in servers.items():
            print('server %s public IP address : %s' % (server_name, ','.join(public_ip_addresses)))


if __name__ == '__main__':
    main()
