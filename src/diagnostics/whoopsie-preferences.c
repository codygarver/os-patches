/* whoopsie
 * 
 * Copyright © 2011 Canonical Ltd.
 * Author: Evan Dandrea <evan.dandrea@canonical.com>
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <gio/gio.h>
#include <stdlib.h>
#include <polkit/polkit.h>

#include "whoopsie-generated.h"

#define CONFIG_PATH "/etc/default/whoopsie"

static GMainLoop* loop = NULL;
static guint loop_shutdown = 0;
static GKeyFile* key_file = NULL;
static PolkitAuthority* authority = NULL;

/* Eventually, it might make sense to move to gsettings with the dconf
 * backend, once it gains PolicyKit support, rather than have a program just
 * to expose an interface to a small configuration file over DBus/PolicyKit.
 * */

/* Once upstart has an interface for disabiling jobs via initctl, we wont need
 * a configuration file anymore */

gboolean
whoopsie_preferences_load_configuration (void)
{
    char* data;
    gsize data_size;
    gboolean ret = TRUE;
    GError* error = NULL;

    if (g_key_file_load_from_file (key_file, CONFIG_PATH,
                                   G_KEY_FILE_KEEP_COMMENTS, NULL)) {
        return TRUE;
    }

    g_key_file_set_boolean (key_file, "General", "report_crashes", TRUE);
    data = g_key_file_to_data (key_file, &data_size, &error);
    if (error) {
        g_print ("Could not process configuration: %s\n", error->message);
        ret = FALSE;
        goto out;
    }
    if (!g_file_set_contents (CONFIG_PATH, data, data_size, &error)) {
        g_print ("Could not write configuration: %s\n", error->message);
        ret = FALSE;
        goto out;
    }

    out:
        if (data)
            g_free (data);
        if (error)
            g_error_free (error);
        return ret;
}

static void
whoopsie_preferences_dbus_notify (WhoopsiePreferences* interface)
{
    GError* error = NULL;
    gboolean report_crashes = FALSE;

    report_crashes = g_key_file_get_boolean (key_file, "General",
                                             "report_crashes", &error);
    if (error) {
        g_warning ("Could not get crashes: %s", error->message);
        g_error_free (error);
    }
    whoopsie_preferences_set_report_crashes (interface, report_crashes);
}

static void
whoopsie_preferences_file_changed (GFileMonitor *monitor, GFile *file,
                                   GFile *other_file,
                                   GFileMonitorEvent event_type,
                                   gpointer user_data)
{
    if (event_type == G_FILE_MONITOR_EVENT_CHANGED) {
        whoopsie_preferences_load_configuration ();
        whoopsie_preferences_dbus_notify (user_data);
    }
}

gboolean
whoopsie_preferences_load (WhoopsiePreferences* interface)
{
    GError* error = NULL;
    GFile* fp = NULL;
    GFileMonitor* file_monitor = NULL;

    fp = g_file_new_for_path (CONFIG_PATH);
    file_monitor = g_file_monitor_file (fp, G_FILE_MONITOR_NONE,
                                        NULL, &error);
    g_signal_connect (file_monitor, "changed",
                      G_CALLBACK (whoopsie_preferences_file_changed),
                      interface);
    if (error) {
        g_print ("Could not set up file monitor: %s\n", error->message);
        g_error_free (error);
    }
    g_object_unref (fp);
    
    key_file = g_key_file_new ();
    whoopsie_preferences_load_configuration ();
}

gboolean
whoopsie_preferences_changed (WhoopsiePreferences* object, GParamSpec* pspec,
                              gpointer user_data)
{
    WhoopsiePreferencesIface* iface;
    gboolean saved_value, new_value;
    GError* error = NULL;
    char* data;
    gsize data_size;

    if (loop_shutdown) {
        g_source_remove (loop_shutdown);
        loop_shutdown = 0;
    }
    loop_shutdown = g_timeout_add_seconds (60, (GSourceFunc) g_main_loop_quit,
                                           loop);

    iface = WHOOPSIE_PREFERENCES_GET_IFACE (object);
    saved_value = g_key_file_get_boolean (key_file, "General", user_data,
                                            &error);
    if (error) {
        g_print ("Could not process configuration: %s\n", error->message);
        return FALSE;
    }
    new_value = iface->get_report_crashes (object);

    if (saved_value != new_value) {
        g_key_file_set_boolean (key_file, "General", user_data, new_value);
        data = g_key_file_to_data (key_file, &data_size, &error);
        if (error) {
            g_print ("Could not process configuration: %s\n", error->message);
            return FALSE;
        }
        if (!g_file_set_contents (CONFIG_PATH, data, data_size, &error)) {
            g_print ("Could not write configuration: %s\n", error->message);
            return FALSE;
        }
    }
}

static gboolean
whoopsie_preferences_on_set_report_crashes (WhoopsiePreferences* object,
                                            GDBusMethodInvocation* invocation,
                                            gboolean report,
                                            gpointer user_data)
{
    whoopsie_preferences_set_report_crashes (object, report);
    whoopsie_preferences_complete_set_report_crashes (object, invocation);
    return TRUE;
}

static gboolean
whoopsie_preferences_authorize_method (GDBusInterfaceSkeleton* interface,
                                       GDBusMethodInvocation* invocation,
                                       gpointer user_data)
{
    PolkitSubject* subject = NULL;
    PolkitAuthorizationResult* result = NULL;
    GError* error = NULL;
    const char* sender = NULL;
    gboolean ret = FALSE;

    sender = g_dbus_method_invocation_get_sender (invocation);
    subject = polkit_system_bus_name_new (sender);
    result = polkit_authority_check_authorization_sync (authority, subject,
                                    "com.ubuntu.whoopsiepreferences.change",
                                    NULL,
                                    POLKIT_CHECK_AUTHORIZATION_FLAGS_NONE,
                                    NULL, &error);
    if (result == NULL) {
        g_dbus_method_invocation_return_error (invocation, G_DBUS_ERROR,
                           G_DBUS_ERROR_AUTH_FAILED, "Could not authorize: %s",
                           error->message);
        g_error_free (error);
        goto out;
    }
    if (!polkit_authorization_result_get_is_authorized (result)) {
        g_dbus_method_invocation_return_error (invocation, G_DBUS_ERROR,
                           G_DBUS_ERROR_AUTH_FAILED, "Not authorized.");
        goto out;
    }
    ret = TRUE;
    out:
        if (result != NULL)
            g_object_unref (result);
        g_object_unref (subject);
        return ret;
}

static void
on_bus_acquired (GDBusConnection* connection, const gchar* name,
                 gpointer user_data)
{
    WhoopsiePreferences* interface;
    GError* error = NULL;

    interface = whoopsie_preferences_skeleton_new ();
    if (!g_dbus_interface_skeleton_export (
                G_DBUS_INTERFACE_SKELETON (interface),
                connection,
                "/com/ubuntu/WhoopsiePreferences", &error)) {

        g_print ("Could not export path: %s\n", error->message);
        g_error_free (error);
        g_main_loop_quit (loop);
        return;
    }

    authority = polkit_authority_get_sync (NULL, &error);
    if (authority == NULL) {
        g_print ("Could not get authority: %s\n", error->message);
        g_error_free (error);
        g_main_loop_quit (loop);
        return;
    }
    loop_shutdown = g_timeout_add_seconds (60, (GSourceFunc) g_main_loop_quit,
                                           loop);

    g_signal_connect (interface, "notify::report-crashes",
                      G_CALLBACK (whoopsie_preferences_changed),
                      "report_crashes");
    g_signal_connect (interface, "handle-set-report-crashes",
                      G_CALLBACK (whoopsie_preferences_on_set_report_crashes),
                      NULL);
    g_signal_connect (interface, "g-authorize-method", G_CALLBACK
                      (whoopsie_preferences_authorize_method), authority);

    whoopsie_preferences_load (interface);
    whoopsie_preferences_dbus_notify (interface);
}

static void
on_name_acquired (GDBusConnection* connection, const gchar* name,
                  gpointer user_data)
{
    g_print ("Acquired the name: %s\n", name);
}

static void
on_name_lost (GDBusConnection* connection, const gchar* name,
              gpointer user_data)
{
    g_print ("Lost the name: %s\n", name);
}

int
main (int argc, char** argv)
{
    guint owner_id;

    if (getuid () != 0) {
        g_print ("This program must be run as root.\n");
        return 1;
    }

    g_type_init();

    owner_id = g_bus_own_name (G_BUS_TYPE_SYSTEM,
                               "com.ubuntu.WhoopsiePreferences",
                               G_BUS_NAME_OWNER_FLAGS_NONE,
                               on_bus_acquired,
                               on_name_acquired,
                               on_name_lost,
                               NULL, NULL);

    loop = g_main_loop_new (NULL, FALSE);
    g_main_loop_run (loop);
    g_bus_unown_name (owner_id);
    g_main_loop_unref (loop);
    if (key_file)
        g_key_file_free (key_file);
    return 0;
}
