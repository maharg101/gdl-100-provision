# -*- coding: utf-8 -*-
"""
test_build_utils.py

Description: Tests for build_utils package.
Written by:  maharg101 on 25th February 2018
"""

import unittest

from build_utils import utils


class TestBuildUtils(unittest.TestCase):

    def test_populate_params_optimal(self):
        """
        Test that populate_params works as expected with optimal inputs.
        """
        params = dict(
            app='hello_world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
        )
        expected_params = dict(
            app='hello_world',
            environment='dev',
            num_servers=1,
            server_size='t1.micro',
            router_name='router_hello_world_dev',
            network_name='network_hello_world_dev',
            subnet_name='subnet_hello_world_dev',
            server_base_name='server_hello_world_dev',
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
            environment='dev 2',
            num_servers=1,
            server_size='t1.micro',
            router_name='router_helloworld-2_dev 2',
            network_name='network_helloworld-2_dev 2',
            subnet_name='subnet_helloworld-2_dev 2',
            server_base_name='server_helloworld-2_dev 2',
        )
        utils.populate_params(params)  # updates in place
        self.assertEqual(params, expected_params)