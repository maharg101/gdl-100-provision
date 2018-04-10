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
                OS_PROJECT_DOMAIN_NAME='fox',
                OS_PASSWORD='hackme',
                OS_PROJECT_ID='183f44dd82457385d4d4d8e702c45661',
                key_name='badman 1337',
                network_name='network-blog-dev',
        )

        expected = yaml.load(
            """\
openstack:
  driver: openstack
  region_name: %(OS_REGION_NAME)s
  auth:
    username: %(OS_USERNAME)s
    password: %(OS_PASSWORD)s
    project_id: %(OS_PROJECT_ID)s
    auth_url: %(OS_AUTH_URL)s
    user_domain_name: %(OS_USER_DOMAIN_NAME)s
    project_domain_name: %(OS_PROJECT_DOMAIN_NAME)s
  networks:
  - name: public
    nat_source: true
  - name: %(network_name)s
    nat_destination: true
""" % params
        )

        returned = salt_utils.generate_openstack_conf(params)

        self.assertEqual(type(returned), type(io.StringIO()))
        self.assertEqual(expected, yaml.load(returned.read()))
