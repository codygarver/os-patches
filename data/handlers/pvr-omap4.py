# -*- coding: utf-8 -*-
# (c) 2008-2010 Canonical Ltd.
# (c) 2012 Linaro Ltd.
# Authors: Ricardo Salveti de Araujo <rsalveti@linaro.org>
#
# Alternatives from nvidia-common, created by
# Alberto Milone <alberto.milone@canonical.com>
#
# License: GPL v2 or later

import logging, os, re, subprocess

from jockey.xorg_driver import XorgDriverHandler
from subprocess import Popen, PIPE, CalledProcessError

# dummy stub for xgettext
def _(x): return x

class Alternatives(object):

    def __init__(self, master_link):
        self._open_egl_drivers_alternative = 'mesa-egl/ld.so.conf'
        self._command = 'update-alternatives'
        self._master_link = master_link

        # Make sure that the PATH environment variable is set
        if not os.environ.get('PATH'):
            os.environ['PATH'] = '/sbin:/usr/sbin:/bin:/usr/bin'

    def list_alternatives(self):
        '''Get the list of alternatives for the master link'''
        dev_null = open('/dev/null', 'w')
        alternatives = []
        p1 = Popen([self._command, '--list', self._master_link],
                   stdout=PIPE, stderr=dev_null)
        p = p1.communicate()[0]
        dev_null.close()
        c = p.split('\n')
        for line in c:
            line.strip() and alternatives.append(line.strip())

        return alternatives

    def get_current_alternative(self):
        '''Get the alternative in use'''
        dev_null = open('/dev/null', 'w')
        current_alternative = None
        p1 = Popen([self._command, '--query', self._master_link],
                   stdout=PIPE, stderr=dev_null)
        p = p1.communicate()[0]
        dev_null.close()
        c = p.split('\n')
        for line in c:
            if line.strip().startswith('Value:'):
                return line.replace('Value:', '').strip()
        return None

    def get_alternative_by_name(self, name, ignore_pattern=None):
        '''Get the alternative link by providing the driver name

        ignore_pattern allows ignoring a substring in the name'''
        if ignore_pattern:
            name = name.replace(ignore_pattern, '')
        alternatives = self.list_alternatives()

        for alternative in alternatives:
            if alternative.split('/')[-2] == name:
                return alternative

        return None

    def get_open_egl_drivers_alternative(self):
        '''Get the alternative link for open EGL/GLES drivers'''
        return self.get_alternative_by_name(self._open_egl_drivers_alternative)

    def set_alternative(self, path):
        '''Tries to set an alternative and returns the boolean exit status'''
        try:
            subprocess.check_call([self._command, '--set',
                                   self._master_link, path])
            self.ldconfig()
        except CalledProcessError:
            return False

        return True

    def ldconfig(self):
        '''Call ldconfig'''
        try:
            subprocess.check_call(['ldconfig'])
        except CalledProcessError:
            return False
        return True

class PVROmap4Driver(XorgDriverHandler):
    def __init__(self, backend, package=None):
        self._free = False

        name=_('PowerVR SGX proprietary graphics driver for OMAP 4')

        XorgDriverHandler.__init__(self, backend, 'omapdrm_pvr', 'pvr-omap4',
            None, None, name=name,
            description=_('3D-accelerated proprietary graphics driver for '
                'OMAP 4 SoCs.'),
            rationale=_('This driver is required to fully utilise the 3D '
                'potential of OMAP 4 powered boards.'))

        self.pkg_alternative = 'pvr-omap4-egl'
        self._module_alias = 'omapdrm_pvr'
        self._alternatives = self._get_alternatives()
        self.omap4_re = re.compile('^Hardware.*OMAP4.*')
        self.needs_kernel_headers = True

    def _get_architecture(self):
        dev_null = open('/dev/null', 'w')
        p1 = Popen(['dpkg', '--print-architecture'], stdout=PIPE,
                   stderr=dev_null)
        p = p1.communicate()[0]
        dev_null.close()
        architecture = p.strip()
        return architecture

    def _get_alternatives(self):
        '''Get multi-arch alternatives names'''
        main_name = "arm-linux-gnueabi_egl_conf"
        if self._get_architecture() == "armhf":
            main_name = "arm-linux-gnueabihf_egl_conf"
        return Alternatives(main_name)

    def available(self):
        '''Check /proc/cpuinfo for an OMAP 4 board.'''
        if XorgDriverHandler.available(self) == False:
            return False

        try:
            for l in open('/proc/cpuinfo'):
                if self.omap4_re.match(l):
                    return True
        except IOError as e:
            logging.error('could not open /proc/cpuinfo: %s' % str(e))

        return False

    def enable(self):
        XorgDriverHandler.enable(self)

        # Set the alternative to PowerVR SGX (EGL)
        pvr_omap4_alternative = self._alternatives.get_alternative_by_name(
                self.pkg_alternative, ignore_pattern='-updates')
        if not pvr_omap4_alternative:
            logging.error('%s: get_alternative_by_name(%s) returned nothing' % (
                self.id(), self.pkg_alternative))
            return
        self._alternatives.set_alternative(pvr_omap4_alternative)

    def enabled(self):
        # See if pvr-omap4 is the current alternative
        target_alternative = \
            self._alternatives.get_alternative_by_name(self.pkg_alternative)
        current_alternative = self._alternatives.get_current_alternative()

        logging.debug('pvr-omap4.enabled(%s): target_alt %s current_alt %s',
                self.module, target_alternative, current_alternative)

        if current_alternative is None:
            logging.debug('current alternative of %s is None, not enabled',
                    self.pkg_alternative)
            return False
        if current_alternative != target_alternative:
            logging.debug('%s is not the alternative in use',
                    self.pkg_alternative)
            return False

        return XorgDriverHandler.enabled(self)

    def disable(self):
        XorgDriverHandler.disable(self)

        # Set the alternative back to open drivers
        open_drivers = self._alternatives.get_open_egl_drivers_alternative()
        logging.debug('pvr-omap4.disable(%s): open_drivers: %s',
                self.module, open_drivers)
        if open_drivers:
            self._alternatives.set_alternative(open_drivers)

        return False

    def enables_composite(self):
        '''Return whether this driver supports the composite extension.'''

        if KernelModuleHandler.module_loaded('omapdrm_pvr'):
            logging.debug('enables_composite(): already using pvr-omap4 '
                    'driver from nondefault package')
            return False

        return True
