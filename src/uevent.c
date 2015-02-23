#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#ifdef HAVE_GUDEV
#include <sys/wait.h>

#include <ctype.h>

#define G_UDEV_API_IS_SUBJECT_TO_CHANGE
#include <gudev/gudev.h>
#include <sys/utsname.h>

gchar *hplip_helper[] = { "/usr/bin/hp-plugin-ubuntu", NULL };

static inline void
g_debug_uevent(const char *msg, ...)
{
   va_list va;
   va_start(va, msg);
   g_logv("uevent",G_LOG_LEVEL_DEBUG, msg, va);
   va_end(va);
}

static gboolean scp_checked = FALSE;

static gboolean
deal_with_scp(GUdevDevice *device)
{
    GError *error = NULL;

    /* only do this once */
    if (scp_checked)
	return FALSE;

    /* check if we just added a printer */
    if ((g_strcmp0(g_udev_device_get_sysfs_attr(device, "bInterfaceClass"), "07") != 0 ||
		g_strcmp0(g_udev_device_get_sysfs_attr(device, "bInterfaceSubClass"), "01") != 0) &&
	    !g_str_has_prefix(g_udev_device_get_name (device), "lp")) {
	g_debug_uevent ("deal_with_scp: devpath=%s: not a printer", g_udev_device_get_sysfs_path(device));
	return FALSE;
    }

    g_debug_uevent ("deal_with_scp: devpath=%s: printer identified", g_udev_device_get_sysfs_path(device));

    scp_checked = TRUE;

    gchar* ps_argv[] = {"ps", "h", "-ocommand", "-Cpython", NULL};
    gchar* ps_out;
    if (!g_spawn_sync (NULL, ps_argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL,
		&ps_out, NULL, NULL, &error)) {
	g_warning ("deal_with_scp: error calling ps: %s", error->message);
	g_error_free (error);
	return TRUE;
    }
    g_debug_uevent ("deal_with_scp: running python processes:%s", ps_out);
    if (strstr (ps_out, "system-config-printer") != NULL) {
	g_debug_uevent ("deal_with_scp: system-config-printer already running");
	return TRUE;
    }

    g_debug_uevent ("deal_with_scp: launching system-config-printer");
    gchar* scp_argv[] = {"system-config-printer-applet", NULL};
    error = NULL;
    if (!g_spawn_async(NULL, scp_argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, &error)) {
	g_warning("%s could not be called: %s", scp_argv[0], error->message);
	g_error_free (error);
    }
    return TRUE;
}

static void
on_uevent (GUdevClient *client,
           gchar *action,
           GUdevDevice *device,
           gpointer user_data)
{
    g_debug_uevent ("uevent.c on_uevent: action=%s, devpath=%s", action, g_udev_device_get_sysfs_path(device));

    if (g_strcmp0 (action, "add") != 0 && g_strcmp0 (action, "change") != 0)
	return;

    if (deal_with_scp(device))
	return;
}

void
uevent_init(void)
{
    const gchar* subsystems[] = {"firmware", "usb", NULL};

    struct utsname u;
    if (uname (&u) != 0) {
	g_warning("uname() failed, not monitoring devices");
	return;
    }

    GUdevClient* gudev = g_udev_client_new (subsystems);
    g_signal_connect (gudev, "uevent", G_CALLBACK (on_uevent), NULL);

    /* cold plug HPLIP devices */
    GList *usb_devices, *elem;
    usb_devices = g_udev_client_query_by_subsystem (gudev, "usb");
    for (elem = usb_devices; elem != NULL; elem = g_list_next(elem)) {
       deal_with_scp(elem->data);
       g_object_unref(elem->data);
    }
    g_list_free(usb_devices);
}
#else
#include <glib.h>
void
uevent_init(void)
{
    g_warning("Printer monitoring disabled.");
}
#endif // HAVE_GUDEV
