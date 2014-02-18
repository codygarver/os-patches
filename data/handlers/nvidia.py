# (c) 2008 Canonical Ltd.
# Authors: Martin Pitt <martin.pitt@ubuntu.com>
#          Alberto Milone <alberto.milone@canonical.com>
# License: GPL v2 or later

import logging, os, os.path

from jockey.handlers import KernelModuleHandler
from jockey.xorg_driver import XorgDriverHandler
from jockey.oslib import OSLib
import XKit
from NvidiaDetector.nvidiadetector import NvidiaDetection
from NvidiaDetector.alternatives import Alternatives
from NvidiaDetector.alternatives import MultiArchUtils
import subprocess

# dummy stub for xgettext
def _(x): return x

class _NvidiaDriverBase(XorgDriverHandler):
    '''Abstract base class for a particular NVidia driver version.'''

    def __init__(self, backend, version):
        self._free = False
        name=_('NVIDIA accelerated graphics driver')
        description=_('3D-accelerated proprietary graphics driver for '
                      'NVIDIA cards. Required if you want to run Unity.')
        rationale=_('This driver is required to fully utilise '
                    'the 3D potential of NVIDIA graphics cards, as well as provide '
                    '2D acceleration of newer cards.\n\n'
                    'You need to install this driver if you wish to use the Unity '
                    'desktop, enable desktop effects, or run software that '
                    'requires 3D acceleration, such as some games.')
        if 'update' in version:
            name=_('NVIDIA accelerated graphics driver (post-release updates)')
        elif 'experimental' in version:
            name=_('NVIDIA accelerated graphics driver (**experimental** beta)')
            description = None
            rationale = None

        XorgDriverHandler.__init__(self, backend, 'nvidia_' + version.replace('-', '_'),
            'nvidia-' + version,
            None, None, {'NoLogo': 'True'},
            remove_modules=['dri', 'GLcore'],
            name=name,
            description=description,
            rationale=rationale)

        self._module_alias = 'nvidia'
        self._recommended = None
        self._do_rebind = False
        (self._alternatives, self._other_alternatives) = self._get_alternatives()
        self.version = version
        self.needs_kernel_headers = True

    def _get_alternatives(self):
        '''Get multi-arch alternatives names'''
        arch_utils = MultiArchUtils()
        main_name = arch_utils.get_main_alternative_name()
        other_name = arch_utils.get_other_alternative_name()
        return Alternatives(main_name), Alternatives(other_name)

    def available(self):
        # we don't offer this driver in a life CD environment, as we will run
        # out of RAM trying to download and install all the packages in the RAM
        # disk.
        if os.path.isdir('/rofs'):
            logging.debug('Disabling Nvidia driver on live system')
            return False

        if self.has_hybrid_graphics:
            # We disable Hybrid Graphics by default unless a specific
            # driver allows it
            logging.debug('Disabling nvidia-%s on a hybrid graphics system' % (self.version))
            return False

        logging.debug('nvidia.available: falling back to default')
        return XorgDriverHandler.available(self)

    def enable_config_hook(self):
        # make sure that RGB path is not in the xorg.conf otherwise xorg will crash
        it = 0
        for section in self.xorg_conf.globaldict['Files']:
            try:
                self.xorg_conf.removeOption('Files', 'RgbPath', position=it)
            except (XKit.xorgparser.OptionException):
                pass
            it += 1
        
        # remove any Disable "dri2" otherwise nvidia-settings and nvidia-xconfig will fail
        module_sections = self.xorg_conf.globaldict['Module']
        have_modules = len(module_sections) > 0
        
        if have_modules:
            for section in module_sections:
                self.xorg_conf.removeOption('Module', 'Disable', value='dri2', position=section)

    def enable(self):
        if self.has_hybrid_graphics:
            # Do not touch xorg.conf on hybrid graphics
            KernelModuleHandler.enable(self)
        else:
            XorgDriverHandler.enable(self)

        # Set the alternative to NVIDIA
        nvidia_alternative = self._alternatives.get_alternative_by_name(self.package)
        if not nvidia_alternative:
            logging.error('%s: get_alternative_by_name(%s) returned nothing' % (
                self.id(), self.package))
            return
        self._alternatives.set_alternative(nvidia_alternative)
        other_nvidia_alternative = self._other_alternatives.get_alternative_by_name(self.package)
        self._other_alternatives.set_alternative(other_nvidia_alternative)

        subprocess.call(['update-initramfs', '-u'])
        subprocess.call(['update-initramfs', '-u', '-k', os.uname()[2]])
 
    def disable(self):
        if self.has_hybrid_graphics:
            # Do not touch xorg.conf on hybrid graphics
            KernelModuleHandler.disable(self)
        else:
            XorgDriverHandler.disable(self)

        if self.package:
            try:
                self.backend.remove_package('nvidia-settings-' + self.version)
            except (ValueError, SystemError):
                pass

        # Set the alternative back to open drivers
        open_drivers = self._alternatives.get_open_drivers_alternative()
        logging.debug('NVidia.disable(%s): open_drivers: %s', self.module, open_drivers)
        if open_drivers:
            self._alternatives.set_alternative(open_drivers)
        other_open_drivers = self._other_alternatives.get_open_drivers_alternative()
        logging.debug('NVidia.disable(%s): other_open_drivers: %s', self.module, other_open_drivers)
        if other_open_drivers:
            self._other_alternatives.set_alternative(other_open_drivers)
        subprocess.call(['update-initramfs', '-u'])       
        subprocess.call(['update-initramfs', '-u', '-k', os.uname()[2]])

        return False
    
    def recommended(self):
        if self._recommended == None:
            nd = NvidiaDetection()
            self._recommended = self.package == nd.selectDriver()
        return self._recommended

    def enabled(self):
        # See if nvidia (e.g. nvidia-current) is the current alternative
        target_alternative = self._alternatives.get_alternative_by_name(self.package)
        current_alternative = self._alternatives.get_current_alternative()
        other_target_alternative = self._other_alternatives.get_alternative_by_name(self.package)
        other_current_alternative = self._other_alternatives.get_current_alternative()

        logging.debug('NVidia(%s).enabled(): target_alt %s current_alt %s other target alt %s other current alt %s', 
                self.module, target_alternative, current_alternative,
                other_target_alternative, other_current_alternative)
        if current_alternative is None:
            return False

        if current_alternative != target_alternative or \
            other_current_alternative != other_target_alternative:
            logging.debug('%s is not the alternative in use', self.module)
            return False

        #if self.xorg_conf has NoneType, AttributeError will be raised
        if not self.xorg_conf:
            logging.debug('%s: xkit object does not exist!', self.module)
            return False

        # Make sure that neither the alias nor the actual module are blacklisted
        if OSLib.inst.module_blacklisted(self._module_alias) or OSLib.inst.module_blacklisted(self.module):
            logging.debug('%s is blacklisted, so not treating as enabled', self.module)
            return False

        kmh_enabled = KernelModuleHandler.enabled(self)
        logging.debug('KMH enabled: %s', str(kmh_enabled))
        return KernelModuleHandler.enabled(self)

    def used(self):
        '''Return if the handler is currently in use.'''

        if self.changed() and self.enabled():
            return False
        
        # See if "nvidia" is loaded and if the alias corresponds to nvidia_$flavour
        return KernelModuleHandler.module_loaded(self._module_alias) and \
               self._alternatives.resolve_module_alias(self._module_alias) == self.module and \
               (self.package is None or OSLib.inst.package_installed(self.package))

    def enables_composite(self):
        '''Return whether this driver supports the composite extension.'''

        # When using an upstream installation, or -new/-legacy etc., we already
        # have composite
        if KernelModuleHandler.module_loaded('nvidia'):
            logging.debug('enables_composite(): already using nvidia driver from nondefault package')
            return False

        # neither vesa nor nv support composite, so safe to say yes here
        return True

class _NvidiaDriverHybridBase(_NvidiaDriverBase):
    '''Abstract base class for NVidia drivers which support Hybrid graphics.'''

    def __init__(self, backend, version):
        _NvidiaDriverBase.__init__(self, backend, version)
        self.hybrid_gfx_pkg = 'nvidia-prime'

    def hybrid_available(self):
        '''See if the OS supports Hybrid Graphics'''
        # Do not provide a driver if Hybrid graphics is available but
        # unsupported (we need at least the lts-raring stack)
        if not self.supports_hybrid_graphics:
            logging.debug('Hybrid graphics system not supported by the OS')
            return False

        # Check that the extra package to enable Hybrid graphics is available
        if not OSLib.inst.package_available(self.hybrid_gfx_pkg):
            logging.debug('prime package not found')
            return False

        return True

    def available(self):
        # we don't offer this driver in a life CD environment, as we will run
        # out of RAM trying to download and install all the packages in the RAM
        # disk.
        if os.path.isdir('/rofs'):
            logging.debug('Disabling Nvidia driver on live system')
            return False

        # See if it's all ready for Hybrid Graphics
        if self.has_hybrid_graphics and not self.hybrid_available():
            return False

        logging.debug('nvidia.available: falling back to default')
        return XorgDriverHandler.available(self)

    def enable(self):
        # First ensure that the package for Hybrid Graphics is
        # installed, if the system supports it
        if self.has_hybrid_graphics:
            try:
                self.backend.install_package(self.hybrid_gfx_pkg)
            except (ValueError, SystemError):
                # Package not available
                logging.error('%s: Unable to install the %s package. '
                              'Hybrid graphics won\'t work.',
                        self.id(), self.hybrid_gfx_pkg)
                return

        _NvidiaDriverBase.enable(self)

    def enabled(self):
        # Check that the extra package to enable Hybrid graphics is
        # installed
        if (self.has_hybrid_graphics and
            not OSLib.inst.package_installed(self.hybrid_gfx_pkg)):
            return False

        return _NvidiaDriverBase.enabled(self)

    def enable_config_hook(self):
        # Do not touch xorg.conf
        pass

    def disable(self):
        # Try to remove the package for Hybrid Graphics if any
        if self.has_hybrid_graphics:
            try:
                self.backend.remove_package(self.hybrid_gfx_pkg)
            except (ValueError, SystemError):
                pass

        _NvidiaDriverBase.disable(self)

class NvidiaDriver331(_NvidiaDriverHybridBase):
    def __init__(self, backend):
        _NvidiaDriverHybridBase.__init__(self, backend, '331')

class NvidiaDriver331Updates(_NvidiaDriverHybridBase):
    def __init__(self, backend):
        _NvidiaDriverHybridBase.__init__(self, backend, '331-updates')

class NvidiaDriver319(_NvidiaDriverHybridBase):
    def __init__(self, backend):
        _NvidiaDriverHybridBase.__init__(self, backend, '319')

class NvidiaDriver319Updates(_NvidiaDriverHybridBase):
    def __init__(self, backend):
        _NvidiaDriverHybridBase.__init__(self, backend, '319-updates')

class NvidiaDriver304(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '304')

class NvidiaDriver304Updates(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '304-updates')

class NvidiaDriverExperimental310(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, 'experimental-310')

class NvidiaDriverExperimental304(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, 'experimental-304')

class NvidiaDriverCurrent(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, 'current')

class NvidiaDriverCurrentUpdates(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, 'current-updates')

class NvidiaDriver173(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '173')

class NvidiaDriver173Updates(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '173-updates')

class NvidiaDriver96(_NvidiaDriverBase):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '96')

    def enable_config_hook(self):
        _NvidiaDriverBase.enable_config_hook(self)

        # ensure we have a screen section
        if len(self.xorg_conf.globaldict['Screen']) == 0:
            screen = self.xorg_conf.makeSection('Screen', identifier='Default Screen')
        
        # version 96 needs AddARGBGLXVisuals
        if self.version == '96':
            self.xorg_conf.addOption('Screen', 'AddARGBGLXVisuals', 'True', optiontype='Option', position=0)

class NvidiaDriver96Updates(NvidiaDriver96):
    def __init__(self, backend):
        _NvidiaDriverBase.__init__(self, backend, '96-updates')

