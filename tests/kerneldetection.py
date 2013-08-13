#
#       kerneldetection.py
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

import jockey.kerneldetection

import fakesysfs
import testarchive


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


class KernelDectionTest(unittest.TestCase):
    '''Test jockey.kerneldetection'''

    def setUp(self):
        '''Create a fake sysfs'''

        self.sys = gen_fakesys()
        os.environ['SYSFS_PATH'] = self.sys.sysfs

        # no custom detection plugins by default
        self.plugin_dir = tempfile.mkdtemp()
        os.environ['UBUNTU_DRIVERS_DETECT_DIR'] = self.plugin_dir

    def tearDown(self):
        try:
            del os.environ['SYSFS_PATH']
        except KeyError:
            pass
        shutil.rmtree(self.plugin_dir)

    def test_linux_headers_detection_chroot(self):
        '''get_linux_headers_metapackage() for test package repository'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-23-generic',
                                extra_tags={'Source': 'linux'})
            archive.create_deb('linux-image-3.2.0-33-generic',
                                extra_tags={'Source': 'linux'})
            archive.create_deb('linux-image-3.5.0-18-generic',
                                extra_tags={'Source':
                                            'linux-lts-quantal'})
            archive.create_deb('linux-image-3.5.0-19-generic',
                                extra_tags={'Source':
                                             'linux-lts-quantal'})
            archive.create_deb('linux-image-generic',
                                extra_tags={'Source':
                                            'linux-meta'})
            archive.create_deb('linux-image-generic-lts-quantal',
                                extra_tags={'Source':
                                            'linux-meta-lts-quantal'})
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-23-generic',
                        'linux-image-3.2.0-33-generic',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-generic-lts-quantal')
        finally:
            chroot.remove()

    def test_linux_headers_detection_names_chroot1(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.2.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-17-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.2.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-17-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-powerpc-smp')
        finally:
            chroot.remove()

    def test_linux_headers_detection_names_chroot2(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.2.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.2.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-powerpc64-smp')
        finally:
            chroot.remove()

    def test_linux_headers_detection_names_chroot3(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.8.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.8.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-omap4')
        finally:
            chroot.remove()

    def test_linux_headers_detection_names_chroot4(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-3-powerpc-e500',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-1-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-2-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-powerpc-smp',
                        'linux-image-3.8.0-3-powerpc-e500',
                        'linux-image-3.8.0-1-powerpc-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-3.8.0-2-powerpc64-smp',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-powerpc-e500')
        finally:
            chroot.remove()

    def test_linux_headers_detection_names_chroot5(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-36-lowlatency-pae',
                                extra_tags={'Source': 'linux-lowlatency'})
            archive.create_deb('linux-image-3.8.0-0-lowlatency',
                                extra_tags={'Source': 'linux-lowlatency'})
            archive.create_deb('linux-image-3.5.0-18-generic',
                                extra_tags={'Source':
                                            'linux-lts-quantal'})
            archive.create_deb('linux-image-3.5.0-19-generic',
                                extra_tags={'Source':
                                             'linux-lts-quantal'})
            archive.create_deb('linux-image-generic',
                                extra_tags={'Source':
                                            'linux-meta'})
            archive.create_deb('linux-image-generic-lts-quantal',
                                extra_tags={'Source':
                                            'linux-meta-lts-quantal'})
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-36-lowlatency-pae',
                        'linux-image-3.8.0-0-lowlatency',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux_headers = kernel_detection.get_linux_headers_metapackage()
            self.assertEqual(linux_headers, 'linux-headers-lowlatency')
        finally:
            chroot.remove()

    def test_linux_detection_chroot(self):
        '''get_linux_metapackage() for test package repository'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-23-generic',
                                extra_tags={'Source': 'linux'})
            archive.create_deb('linux-image-3.2.0-33-generic',
                                extra_tags={'Source': 'linux'})
            archive.create_deb('linux-image-3.5.0-18-generic',
                                extra_tags={'Source':
                                            'linux-lts-quantal'})
            archive.create_deb('linux-image-3.5.0-19-generic',
                                extra_tags={'Source':
                                             'linux-lts-quantal'})
            archive.create_deb('linux-image-generic',
                                extra_tags={'Source':
                                            'linux-meta'})
            archive.create_deb('linux-image-generic-lts-quantal',
                                extra_tags={'Source':
                                            'linux-meta-lts-quantal'})
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-23-generic',
                        'linux-image-3.2.0-33-generic',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-generic-lts-quantal')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot1(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.2.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-17-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.2.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-17-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-powerpc-smp')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot2(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.2.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.2.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-powerpc64-smp')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot3(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-nexus7',
                                extra_tags={'Source': 'linux-meta-nexus7'})
            archive.create_deb('linux-image-3.1.10-9-nexus7',
                                extra_tags={'Source': 'linux-nexus7'})
            archive.create_deb('linux-image-omap4',
                                extra_tags={'Source':
                                            'linux-meta-ti-omap4'})
            archive.create_deb('linux-image-3.8.0-1419-omap4',
                                extra_tags={'Source':
                                            'linux-ti-omap4'})
            archive.create_deb('linux-image-3.5.0-17-highbank',
                                extra_tags={'Source':
                                             'linux'})
            archive.create_deb('linux-image-highbank',
                                extra_tags={'Source':
                                             'linux-meta-highbank'})
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc-smp'})
            archive.create_deb('linux-image-3.5.0-18-powerpc-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-meta-powerpc64-smp'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux'})
            archive.create_deb('linux-image-ac100',
                                extra_tags={'Source':
                                            'linux-meta-ac100'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-nexus7',
                        'linux-image-3.1.10-9-nexus7',
                        'linux-image-omap4',
                        'linux-image-3.8.0-1419-omap4',
                        'linux-image-highbank',
                        'linux-image-3.5.0-17-highbank',
                        'linux-image-powerpc-smp',
                        'linux-image-3.5.0-18-powerpc-smp',
                        'linux-image-powerpc64-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-ac100',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-omap4')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot4(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-3-powerpc-e500',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-1-powerpc-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.5.0-19-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.8.0-2-powerpc64-smp',
                                extra_tags={'Source':
                                            'linux-ppc'})
            archive.create_deb('linux-image-3.0.27-1-ac100',
                                extra_tags={'Source':
                                            'linux-ac100'})

            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-powerpc-smp',
                        'linux-image-3.8.0-3-powerpc-e500',
                        'linux-image-3.8.0-1-powerpc-smp',
                        'linux-image-3.5.0-19-powerpc64-smp',
                        'linux-image-3.8.0-2-powerpc64-smp',
                        'linux-image-3.0.27-1-ac100'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-powerpc-e500')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot5(self):
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-36-lowlatency-pae',
                                extra_tags={'Source': 'linux-lowlatency'})
            archive.create_deb('linux-image-3.8.0-0-lowlatency',
                                extra_tags={'Source': 'linux-lowlatency'})
            archive.create_deb('linux-image-3.5.0-18-generic',
                                extra_tags={'Source':
                                            'linux-lts-quantal'})
            archive.create_deb('linux-image-3.5.0-19-generic',
                                extra_tags={'Source':
                                             'linux-lts-quantal'})
            archive.create_deb('linux-image-generic',
                                extra_tags={'Source':
                                            'linux-meta'})
            archive.create_deb('linux-image-generic-lts-quantal',
                                extra_tags={'Source':
                                            'linux-meta-lts-quantal'})
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-36-lowlatency-pae',
                        'linux-image-3.8.0-0-lowlatency',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-lowlatency')
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot6(self):
        '''get_linux_metapackage() does not raise a KeyError'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-36-lowlatency-pae')
            archive.create_deb('linux-image-3.8.0-0-lowlatency')
            archive.create_deb('linux-image-3.5.0-18-generic')
            archive.create_deb('linux-image-3.5.0-19-generic')
            archive.create_deb('linux-image-generic')
            archive.create_deb('linux-image-generic-lts-quantal')
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-36-lowlatency-pae',
                        'linux-image-3.8.0-0-lowlatency',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            try:
                kernel_detection.get_linux_metapackage()
            except KeyError:
                self.fail("get_linux_metapackage() raised KeyError!")
        finally:
            chroot.remove()

    def test_linux_detection_names_chroot7(self):
        '''get_linux_metapackage() continues despite a KeyError'''
        chroot = aptdaemon.test.Chroot()
        try:
            chroot.setup()
            chroot.add_test_repository()
            archive = gen_fakearchive()
            archive.create_deb('linux-image-3.2.0-36-lowlatency-pae')
            archive.create_deb('linux-image-3.8.0-0-lowlatency',
                                extra_tags={'Source': 'linux-lowlatency'})
            archive.create_deb('linux-image-3.5.0-18-generic')
            archive.create_deb('linux-image-3.5.0-19-generic')
            archive.create_deb('linux-image-generic')
            archive.create_deb('linux-image-generic-lts-quantal')
            chroot.add_repository(archive.path, True, False)

            cache = apt.Cache(rootdir=chroot.path)

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, '')

            # Install kernel packages
            for pkg in ('linux-image-3.2.0-36-lowlatency-pae',
                        'linux-image-3.8.0-0-lowlatency',
                        'linux-image-3.5.0-18-generic',
                        'linux-image-3.5.0-19-generic',
                        'linux-image-generic',
                        'linux-image-generic-lts-quantal'):
                cache[pkg].mark_install()

            kernel_detection = jockey.kerneldetection.KernelDetection(cache)
            linux = kernel_detection.get_linux_metapackage()
            self.assertEqual(linux, 'linux-lowlatency')
        finally:
            chroot.remove()

if __name__ == '__main__':
    unittest.main()
