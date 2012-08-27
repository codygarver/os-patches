# -*- coding: utf-8 -*-
# (c) 2008 Canonical Ltd.
# Authors: Martin Pitt <martin.pitt@ubuntu.com>
#          Alberto Milone <alberto.milone@canonical.com>
# License: GPL v2 or later

import logging, os, os.path

import XKit.xorgparser
from jockey.xorg_driver import XorgDriverHandler
from NvidiaDetector.alternatives import Alternatives
from NvidiaDetector.alternatives import MultiArchUtils
import subprocess

# dummy stub for xgettext
def _(x): return x

class CdvDriver(XorgDriverHandler):
    def __init__(self, backend, package=None):
        self._free = False

        name=_('Intel Cedarview graphics driver')

        XorgDriverHandler.__init__(self, backend, 'cedarview_gfx',
            'cedarview-graphics-drivers', None, None, add_modules=['glx'],
            disable_modules=[], name=name,
            description=_('3D-accelerated proprietary graphics driver for '
                'Intel Cedarview cards.'),
            rationale=_('This driver is required to fully utilise the 3D '
                'potential of some Intel Cedarview cards, as well as provide '
                '2D acceleration of newer cards.'))

        self._alternatives = self._get_alternatives()
        self.needs_kernel_headers = True
        self.alternative_name = 'intel-cdv'

    def _get_alternatives(self):
        '''Get multi-arch alternatives names'''
        main_name = 'i386-linux-gnu_egl_conf'
        return Alternatives(main_name)

    def available(self):
        # we don't offer cdv in a life CD environment, as we will run out of
        # RAM trying to download and install all the packages in the RAM disk.
        if os.path.isdir('/rofs'):
            logging.debug('Disabling cdv driver on live system')
            return False

        logging.debug('cdv.available: falling back to default')
        return XorgDriverHandler.available(self)

    def enable(self):
        XorgDriverHandler.enable(self)
        
        # Set the alternative to cdv
        cdv_alternative = self._alternatives.get_alternative_by_name(
            self.alternative_name, ignore_pattern='-updates')
        if not cdv_alternative:
            logging.error('%s: get_alternative_by_name(%s) returned nothing' % (
                self.id(), self.package))
            return
        self._alternatives.set_alternative(cdv_alternative)
        subprocess.call(['update-initramfs', '-u'])
        subprocess.call(['update-initramfs', '-u', '-k', os.uname()[2]])

    def enabled(self):
        # See if cdv is the current alternative
        target_alternative = \
            self._alternatives.get_alternative_by_name(self.alternative_name)
        current_alternative = self._alternatives.get_current_alternative()

        logging.debug('cdv.enabled(%s): target_alt %s current_alt %s',
                self.module, target_alternative, current_alternative)

        if current_alternative is None:
            logging.debug('current alternative of %s is None, not enabled',
                self.module)
            return False
        if current_alternative != target_alternative:
            logging.debug('%s is not the alternative in use', self.module)
            return False

        return XorgDriverHandler.enabled(self)

    def disable(self):
        XorgDriverHandler.disable(self)
        # make sure that 'cedarview-drm' is removed too
        self.backend.remove_package('cedarview-drm')

        # Set the alternative back to open drivers
        open_drivers = self._alternatives.get_open_drivers_alternative()
        logging.debug('cdv.disable(%s): open_drivers: %s',
            self.module, open_drivers)
        if open_drivers:
            self._alternatives.set_alternative(open_drivers)

        subprocess.call(['update-initramfs', '-u'])
        subprocess.call(['update-initramfs', '-u', '-k', os.uname()[2]])

        return False
