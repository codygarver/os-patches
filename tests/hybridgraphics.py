#
#       hybridgraphics.py
#
#       Copyright 2013 Canonical Ltd.
#
#       Author: Alberto Milone <alberto.milone@canonical.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import os
import shutil
import tempfile
import unittest
import apt
import aptdaemon.test
import aptdaemon.pkcompat
import jockey.handlers, jockey.backend
import fakesysfs
import testarchive

from jockey.oslib import OSLib
from jockey.xorg_driver import XorgDriverHandler

def gen_fakesys():
    '''Generate a fake SysFS object for testing'''

    s = fakesysfs.SysFS()
    # covered by vanilla.deb
    s.add('pci', 'white', {'modalias': 'pci:v00001234d00sv00000001sd00bc00sc00i00'})
    # covered by chocolate.deb
    s.add('usb', 'black', {'modalias': 'usb:v9876dABCDsv01sd02bc00sc01i05'})
    # covered by nvidia-{current,old}.deb
    s.add('pci', 'graphics', {'modalias': 'pci:nvidia',
                              'vendor': '0x10DE',
                              'device': '0x10C3',
                             })
    # not covered by any driver package
    s.add('pci', 'grey', {'modalias': 'pci:vDEADBEEFd00'})
    s.add('ssb', 'yellow', {}, {'MODALIAS': 'pci:vDEADBEEFd00'})

    return s


def gen_fakearchive():
    '''Generate a fake archive for testing'''

    a = testarchive.Archive()
    a.create_deb('vanilla', extra_tags={'Modaliases':
        'vanilla(pci:v00001234d*sv*sd*bc*sc*i*, pci:v0000BEEFd*sv*sd*bc*sc*i*)'})
    a.create_deb('chocolate', dependencies={'Depends': 'xserver-xorg-core'},
        extra_tags={'Modaliases':
            'chocolate(usb:v9876dABCDsv*sd*bc00sc*i*, pci:v0000BEEFd*sv*sd*bc*sc*i00)'})

    # packages for testing X.org driver ABI installability
    a.create_deb('xserver-xorg-core', version='99:1',  # higher than system installed one
            dependencies={'Provides': 'xorg-video-abi-4'})
    a.create_deb('nvidia-current', dependencies={'Depends': 'xorg-video-abi-4'},
                 extra_tags={'Modaliases': 'nv(pci:nvidia, pci:v000010DEd000010C3sv00sd01bc03sc00i00)'})
    a.create_deb('nvidia-old', dependencies={'Depends': 'xorg-video-abi-3'},
                 extra_tags={'Modaliases': 'nv(pci:nvidia, pci:v000010DEd000010C3sv00sd01bc03sc00i00)'})

    # packages not covered by modalises, for testing detection plugins
    a.create_deb('special')
    a.create_deb('picky')
    a.create_deb('special-uninst', dependencies={'Depends': 'xorg-video-abi-3'})

    return a

def is_installed(package, cache):
    installed = False

    try:
        installed = cache[package].marked_install
    except KeyError:
        # The package is not available
        pass
    return installed

class HybridDectionTest(unittest.TestCase):
    '''Test jockey hybrid graphics support'''

    def setUp(self):
        '''Create a fake sysfs'''

        self.sys = gen_fakesys()
        os.environ['SYSFS_PATH'] = self.sys.sysfs

        # no custom detection plugins by default
        self.plugin_dir = tempfile.mkdtemp()
        os.environ['UBUNTU_DRIVERS_DETECT_DIR'] = self.plugin_dir

        self.backend = jockey.backend.Backend()

    def tearDown(self):
        try:
            del os.environ['SYSFS_PATH']
        except KeyError:
            pass
        shutil.rmtree(self.plugin_dir)


    def test_has_hybrid_graphics_chroot_1(self):
        '''_has_hybrid_gfx() for lts-raring stack'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core-lts-raring',
                        'linux-image-generic-lts-raring'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.9.0'
            x_abi = '13'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assert_(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0300: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assert_(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0300: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assert_(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0300: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assert_(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0300: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assert_(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()

    def test_has_hybrid_graphics_chroot_2(self):
        '''_has_hybrid_gfx() for lts-quantal stack'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('linux-image-generic-lts-quantal')
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core-lts-quantal',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.5.0-36-generic'
            x_abi = '13'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assertFalse(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0300: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assertFalse(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0300: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assertFalse(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0300: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assertFalse(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0300: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assertFalse(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()

    def test_has_hybrid_graphics_chroot_3(self):
        '''_has_hybrid_gfx() for 12.04.0 stack'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('linux-image-generic')
            archive.create_deb('linux-image-generic-lts-quantal')
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core',
                        'linux-image-generic'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.2.0.49.59'
            x_abi = '11'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assertFalse(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0300: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assertFalse(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0300: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assertFalse(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0300: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assertFalse(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0300: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assertFalse(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()

    def test_has_hybrid_graphics_chroot_4(self):
        '''_has_hybrid_gfx() for lts-raring stack, different pci class'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core-lts-raring',
                        'linux-image-generic-lts-raring'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.9.0'
            x_abi = '13'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assert_(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0302: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assert_(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0302: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assert_(prime.supports_hybrid_graphics)

            # Intel + Nvidia - different pci class
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0301: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assert_(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0380: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assert_(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0301: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assert_(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()

    def test_has_hybrid_graphics_chroot_5(self):
        '''_has_hybrid_gfx() for lts-saucy stack'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-saucy',
                                extra_tags={'Provides':
                                'xorg-video-abi-14, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-trusty',
                                extra_tags={'Provides':
                                'xorg-video-abi-15, xserver-xorg-core'})
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')
            archive.create_deb('linux-image-generic-lts-trusty')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core-lts-saucy',
                        'linux-image-generic-lts-saucy'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.11.0'
            x_abi = '14'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assert_(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0300: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assert_(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0300: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assert_(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0300: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assert_(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0300: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assert_(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()

    def test_has_hybrid_graphics_chroot_5(self):
        '''_has_hybrid_gfx() for lts-trusty stack'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('xserver-xorg-core',
                                extra_tags={'Provides':
                                'xorg-video-abi-11, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-quantal',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-raring',
                                extra_tags={'Provides':
                                'xorg-video-abi-13, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-saucy',
                                extra_tags={'Provides':
                                'xorg-video-abi-14, xserver-xorg-core'})
            archive.create_deb('xserver-xorg-core-lts-trusty',
                                extra_tags={'Provides':
                                'xorg-video-abi-15, xserver-xorg-core'})
            archive.create_deb('linux-image-generic-lts-raring')
            archive.create_deb('linux-image-generic-lts-saucy')
            archive.create_deb('linux-image-generic-lts-trusty')

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            # Install kernel packages
            for pkg in ('xserver-xorg-core-lts-trusty',
                        'linux-image-generic-lts-trusty'):
                cache[pkg].mark_install()

            # Set fake kernel and X ABI
            kernel = '3.13.0'
            x_abi = '15'

            # Single GPU
            pcilist_single = ['00:01.0 0300: 8086:0162 (rev 09)']

            single = XorgDriverHandler(self.backend, 'vanilla3d0',
                    'mesa-vanilla0', 'v3d0',
                    'vanilla0',
                    name='Vanilla accelerated graphics driver0',
                    fake_pcilist=pcilist_single,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(single.has_hybrid_graphics)
            self.assert_(single.supports_hybrid_graphics)

            # Completely Unsupported GPU vendors
            pcilist_multi = ['00:01.0 0300: 1111:0162 (rev 09)',
                             '00:02.0 0300: 1022:0163']

            multi = XorgDriverHandler(self.backend, 'vanilla3d00',
                    'mesa-vanilla00', 'v3d00',
                    'vanilla00',
                    name='Vanilla accelerated graphics driver00',
                    fake_pcilist=pcilist_multi,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assertFalse(multi.has_hybrid_graphics)
            self.assert_(multi.supports_hybrid_graphics)

            # Intel + Nvidia
            pcilist_prime = ['00:01.0 0300: 8086:0162 (rev 09)',
                             '00:02.0 0300: 10de:0163']

            prime = XorgDriverHandler(self.backend, 'vanilla3d1',
                    'mesa-vanilla1', 'v3d1',
                    'vanilla1',
                    name='Vanilla accelerated graphics driver1',
                    fake_pcilist=pcilist_prime,
                    fake_kernel=kernel, fake_xabi=x_abi,
                    fake_inst_func=is_installed,
                    fake_apt_cache=cache)

            self.assert_(prime.has_hybrid_graphics)
            self.assert_(prime.supports_hybrid_graphics)

            # Intel + AMD
            pcilist_pxpress = ['00:01.0 0300: 8086:0162 (rev 09)',
                               '00:02.0 0300: 1002:0163']
            pxpress = XorgDriverHandler(self.backend, 'vanilla3d2',
                     'mesa-vanilla2', 'v3d2',
                     'vanilla2',
                     name='Vanilla accelerated graphics driver2',
                     fake_pcilist=pcilist_pxpress,
                     fake_kernel=kernel, fake_xabi=x_abi,
                     fake_inst_func=is_installed,
                     fake_apt_cache=cache)

            self.assert_(pxpress.has_hybrid_graphics)
            self.assert_(pxpress.supports_hybrid_graphics)

            # AMD + AMD
            pcilist_pxpress_noconf = ['00:01.0 0300: 1002:0162 (rev 09)',
                                      '00:02.0 0300: 1002:0163']
            pxpress_noconf = XorgDriverHandler(self.backend, 'vanilla3d3',
                            'mesa-vanilla3', 'v3d3',
                            'vanilla3',
                            name='Vanilla accelerated graphics driver3',
                            fake_pcilist=pcilist_pxpress_noconf,
                            fake_kernel=kernel, fake_xabi=x_abi,
                            fake_inst_func=is_installed,
                            fake_apt_cache=cache)

            self.assert_(pxpress_noconf.has_hybrid_graphics)
            self.assert_(pxpress_noconf.supports_hybrid_graphics)

        finally:
            chroot.remove()


if __name__ == '__main__':
    unittest.main()
