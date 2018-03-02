# -*- coding: utf-8 -*-
"""
test_build_utils.py

Description: Tests for build_utils package.
Written by:  maharg101 on 25th February 2018
"""

import unittest

from build_utils import utils


class TestPopulateParams(unittest.TestCase):

    def test_populate_params_optimal_underscore(self):
        """
        Test that populate_params works as expected with optimal inputs including underscores.
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
        utils.populate_params(params)  # updates in place
        self.assertEqual(params, expected_params)

    def test_populate_params_unusual_input(self):
        """
        Test that populate_params works as expected with not-so-optimal inputs.
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
        utils.populate_params(params)  # updates in place
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