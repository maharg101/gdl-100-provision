# -*- coding: utf-8 -*-
"""
test_build_utils.py

Description: Tests for build_utils.utils module.
Written by:  maharg101 on 25th February 2018
"""

import unittest

from build_utils import utils


class TestPopulateParamsFromConstructorArgs(unittest.TestCase):

    def test_populate_params_from_constructor_args_optimal_underscore(self):
        """
        Test that populate_params_from_constructor_args works as expected with optimal inputs including underscores.
        """
        params = dict(
            app='hello_world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
        )
        expected_params = dict(
            app='hello-world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
            router_name='router-hello-world-dev',
            network_name='network-hello-world-dev',
            subnet_name='subnet-hello-world-dev',
            server_base_name='hello-world-dev',
        )
        utils.populate_params_from_constructor_args(params)  # updates in place
        self.assertEqual(params, expected_params)

    def test_populate_params_from_constructor_args_unusual_input(self):
        """
        Test that populate_params_from_constructor_args works as expected with not-so-optimal inputs.
        """
        params = dict(
            app='%%hello\tworld££~-2',
            environment='%%dev{} 2',
            num_servers=1,
            server_size='t1.micro',
        )
        expected_params = dict(
            app='helloworld-2',
            environment='dev-2',
            num_servers=1,
            server_size='t1.micro',
            router_name='router-helloworld-2-dev-2',
            network_name='network-helloworld-2-dev-2',
            subnet_name='subnet-helloworld-2-dev-2',
            server_base_name='helloworld-2-dev-2',
        )
        utils.populate_params_from_constructor_args(params)  # updates in place
        self.assertEqual(params, expected_params)


class TestConstructServerName(unittest.TestCase):

    def test_construct_server_name_integer_postfix(self):
        """
        Test that construct_server_name works as expected with an integer postfix.
        """
        params = dict(
            app='hello-world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
            router_name='router-hello-world_dev',
            network_name='network-hello-world-dev',
            subnet_name='subnet-hello-world-dev',
            server_base_name='hello-world-dev',
        )
        self.assertEqual(
            utils.construct_server_name(params, 0),
            '0-hello-world-dev'
        )

    def test_construct_server_name_string_postfix(self):
        """
        Test that construct_server_name works as expected with a string postfix.
        """
        params = dict(
            app='hello-world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
            router_name='router-hello-world-dev',
            network_name='network-hello-world-dev',
            subnet_name='subnet-hello-world-dev',
            server_base_name='hello-world-dev',
        )
        self.assertEqual(
            utils.construct_server_name(params, 'foo'),
            'foo-hello-world-dev'
        )


class TestPopulateOpenStackParamsFromEnviron(unittest.TestCase):

    def test_populate_openstack_params_from_environ(self):
        """
        Test that populate_openstack_params_from_environ works as expected.
        :return:
        """
        params = dict(
            foo='bar',
        )
        env_dict = dict(
            OS_AUTH_URL='https://some.cloud/foo/auth',
            OS_IDENTITY_API_VERSION=3,
            OS_REGION_NAME='RegionX',
            OS_USERNAME='flateric',
            OS_USER_DOMAIN_NAME='badger',
            OS_PASSWORD='hackme',
            IRRELEVANT='blah',
        )
        expected_params = dict(
            foo='bar',
            OS_AUTH_URL='https://some.cloud/foo/auth',
            OS_IDENTITY_API_VERSION=3,
            OS_REGION_NAME='RegionX',
            OS_USERNAME='flateric',
            OS_USER_DOMAIN_NAME='badger',
            OS_PASSWORD='hackme',
        )
        utils.populate_openstack_params_from_environ(params, env_dict)  # updates in place
        self.assertEqual(params, expected_params)