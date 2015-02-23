#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <glib.h>
#include <libnotify/notify.h>

#include "update-notifier.h"

static gint
show_notification ()
{
	NotifyNotification *n;

	/* Create and show the notification */
	n = notify_notification_new (_("Network service discovery disabled"),
                                     _("Your current network has a .local "
                                       "domain, which is not recommended "
                                       "and incompatible with the Avahi "
                                       "network service discovery. The service "
                                       "has been disabled."
				       ),
				     GTK_STOCK_DIALOG_INFO);
	notify_notification_set_timeout (n, 60000);
	notify_notification_show (n, NULL);
	g_object_unref (n);

	return FALSE;
}

int
main ()
{

    notify_init("update-notifier");
    bindtextdomain(PACKAGE, PACKAGE_LOCALE_DIR);
    bind_textdomain_codeset(PACKAGE, "UTF-8");
    textdomain(PACKAGE);
    if (g_file_test ("/var/run/avahi-daemon/disabled-for-unicast-local", G_FILE_TEST_EXISTS)) {
        show_notification();
        return 0;
    } else
    {
        return 1;
    }
}
