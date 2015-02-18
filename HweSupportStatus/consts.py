
import datetime
import gettext
gettext.install("update-manager")
from gettext import gettext as _



# the day on which the PRECISE (12.04) HWE stack goes out of support
PRECISE_HWE_EOL_DATE = datetime.date(2014, 8, 7)

# the date 14.04.1 is available
TRUSTY_DOT1_DATE = datetime.date(2014, 7, 16)

# the month in wich PRECISE (12.04) goes out of support
PRECISE_EOL_DATE = datetime.date(2017, 4, 1)


class Messages:
    UM_UPGRADE = _("""
There is a graphics stack installed on this system. An upgrade to a 
supported (or longer supported) configuration will become available
on %(date)s and can be invoked by running 'update-manager' in the
Dash.
    """) % {'date': TRUSTY_DOT1_DATE.isoformat()
           }

    APT_UPGRADE = _("""
To upgrade to a supported (or longer supported) configuration:

* Upgrade from Ubuntu 12.04 LTS to Ubuntu 14.04 LTS by running:
sudo do-release-upgrade %s

OR

* Install a newer HWE version by running:
sudo apt-get install %s

and reboot your system.""")

    # this message is shown if there is no clear upgrade path via a
    # meta pkg that we recognize
    APT_SHOW_UNSUPPORTED = _("""
The following packages are no longer supported:
 %s

Please upgrade them to a supported HWE stack or remove them if you
no longer need them.
""")

    HWE_SUPPORTED = _("Your Hardware Enablement Stack (HWE) is "
                      "supported until %(month)s %(year)s.") % {
                          'month': PRECISE_EOL_DATE.strftime("%B"),
                          'year': PRECISE_EOL_DATE.year,
                          }

    HWE_SUPPORT_ENDS = _("""
Your current Hardware Enablement Stack (HWE) is going out of support
on %s.  After this date security updates for critical parts (kernel
and graphics stack) of your system will no longer be available.

For more information, please see:
http://wiki.ubuntu.com/1204_HWE_EOL
""") % PRECISE_HWE_EOL_DATE.isoformat()

    HWE_SUPPORT_HAS_ENDED = _("""
Your current Hardware Enablement Stack (HWE) is no longer supported
since %s.  Security updates for critical parts (kernel
and graphics stack) of your system are no longer available.

For more information, please see:
http://wiki.ubuntu.com/1204_HWE_EOL
""") % PRECISE_HWE_EOL_DATE.isoformat()
