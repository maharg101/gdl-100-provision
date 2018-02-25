# -*- coding: utf-8 -*-
"""
test_openstack_infrastructure.py

Description: Tests for openstack_infrastructure package.
Written by:  maharg101 on 25th February 2018
"""

import unittest

from openstack_infrastructure import facade as osf


class TestValidateImageFlavorCombination(unittest.TestCase):

    def setUp(self):
        self.os_facade = osf.OpenStackFacade()

    def test_valid_image_flavour_ram_disk_ok(self):
        """
        Test that validate_image_flavor_combination works as expected when both ram and disk are sufficient.
        """
        class Image(object):
            name = 'm1.tiny'
            min_ram = 5
            min_disk = 5

        class Flavor(object):
            name = 'Foo OS'
            ram = 640  # should be enough for anyone
            disk = 1024

        self.assertEqual(
            self.os_facade.validate_image_flavor_combination(Image(), Flavor()),
            None  # no message is returned, meaning everything is good :)
        )

    def test_valid_image_flavour_ram_disk_insufficient(self):
        """
        Test that validate_image_flavor_combination works as expected when both ram and disk are insufficient.
        """
        class Image(object):
            name = 'Foo OS'
            min_ram = 5
            min_disk = 5

        class Flavor(object):
            name = 'm1.pico'
            ram = 1
            disk = 1

        self.assertEqual(
            self.os_facade.validate_image_flavor_combination(Image(), Flavor()),
            'm1.pico does not have the minimum recommended RAM or disk for Foo OS'
        )

    def test_valid_image_flavour_ram_insufficient(self):
        """
        Test that validate_image_flavor_combination works as expected when both ram and disk are insufficient.
        """
        class Image(object):
            name = 'Foo OS'
            min_ram = 5
            min_disk = 5

        class Flavor(object):
            name = 'm1.pico'
            ram = 1
            disk = 1024

        self.assertEqual(
            self.os_facade.validate_image_flavor_combination(Image(), Flavor()),
            'm1.pico does not have the minimum recommended RAM for Foo OS'
        )

    def test_valid_image_flavour_disk_insufficient(self):
        """
        Test that validate_image_flavor_combination works as expected when both ram and disk are insufficient.
        """
        class Image(object):
            name = 'Foo OS'
            min_ram = 5
            min_disk = 5

        class Flavor(object):
            name = 'm1.pico'
            ram = 640
            disk = 1

        self.assertEqual(
            self.os_facade.validate_image_flavor_combination(Image(), Flavor()),
            'm1.pico does not have the minimum recommended disk for Foo OS'
        )

