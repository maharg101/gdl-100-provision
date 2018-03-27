# -*- coding: utf-8 -*-
"""
test_build_salt_utils.py

Description: Tests for build_utils.salt_utils module.
Written by:  maharg101 on 27th March 2018
"""

import io
import unittest
import yaml

from build_utils import salt_utils


class TestGenerateOpenStackConf(unittest.TestCase):

    def test_generate_openstack_conf(self):
        """
        Test that generate_openstack_conf works as expected.
        """
        params = dict(
                OS_AUTH_URL='https://some.cloud/foo/auth',
                OS_IDENTITY_API_VERSION=3,
                OS_REGION_NAME='RegionX',
                OS_USERNAME='flateric',
                OS_USER_DOMAIN_NAME='badger',
                OS_PASSWORD='hackme',
                key_name='badman 1337',
                fixed_network_id='d34db33f-80zx-789c-a1a2-1d12345a123d',
        )

        expected = yaml.load(
            """\
openstack_config:
  auth_version: %(OS_IDENTITY_API_VERSION)d
  compute_name: nova
  compute_region: %(OS_REGION_NAME)s
  domain: %(OS_USER_DOMAIN_NAME)s
  driver: openstack
  identity_url: %(OS_AUTH_URL)s/auth/tokens
  insecure: false
  networks:
  - fixed:
    - %(fixed_network_id)s
  - floating:
    - public
  password: %(OS_PASSWORD)s
  service_type: compute
  ssh_key_file: /etc/salt/pki/master/master.pem
  ssh_key_name: %(key_name)s
  tenant: %(OS_USERNAME)s
  user: %(OS_USERNAME)s
""" % params
        )

        returned = salt_utils.generate_openstack_conf(params)

        self.assertEqual(type(returned), type(io.StringIO()))
        self.assertEqual(expected, yaml.load(returned.read()))
