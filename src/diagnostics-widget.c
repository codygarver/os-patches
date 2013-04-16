#include <gtk/gtk.h>
#include <gio/gio.h>
#include <polkit/polkit.h>

#include "diagnostics/whoopsie-generated.h"

static WhoopsiePreferences* proxy = NULL;

#define POL_PATH "com.ubuntu.whoopsiepreferences.change"
#define PRIVACY_URL "http://www.ubuntu.com/aboutus/privacypolicy"

#define WHOOPSIE_DAISY_TYPE_PREFERENCES whoopsie_daisy_preferences_get_type()
#define WHOOPSIE_DAISY_PREFERENCES(obj) \
    (G_TYPE_CHECK_INSTANCE_CAST ((obj), \
    WHOOPSIE_DAISY_TYPE_PREFERENCES, WhoopsieDaisyPreferences))
#define WHOOPSIE_DAISY_PREFERENCES_PRIVATE(o) \
    (G_TYPE_INSTANCE_GET_PRIVATE ((o), WHOOPSIE_DAISY_TYPE_PREFERENCES, WhoopsieDaisyPreferencesPrivate))

GType whoopsie_daisy_preferences_get_type (void) G_GNUC_CONST;

typedef struct _WhoopsieDaisyPreferences WhoopsieDaisyPreferences;
typedef struct _WhoopsieDaisyPreferencesClass WhoopsieDaisyPreferencesClass;
typedef struct _WhoopsieDaisyPreferencesPrivate WhoopsieDaisyPreferencesPrivate;

struct _WhoopsieDaisyPreferencesPrivate
{
    GtkBuilder* builder;
    GPermission* permission;
};

struct _WhoopsieDaisyPreferences
{
    GtkBox parent;
    WhoopsieDaisyPreferencesPrivate* priv;
};

struct _WhoopsieDaisyPreferencesClass
{
    GtkBoxClass parent_class;
};

G_DEFINE_TYPE (WhoopsieDaisyPreferences, whoopsie_daisy_preferences, GTK_TYPE_BOX)

static void
whoopsie_daisy_preferences_dispose (GObject* object)
{
    WhoopsieDaisyPreferencesPrivate* priv = WHOOPSIE_DAISY_PREFERENCES (object)->priv;

    if (priv->builder) {
        g_object_unref (priv->builder);
        priv->builder = NULL;
    }
    if (priv->permission) {
        g_object_unref (priv->permission);
        priv->permission = NULL;
    }
}

static void
whoopsie_daisy_preferences_class_init (WhoopsieDaisyPreferencesClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    g_type_class_add_private (klass, sizeof (WhoopsieDaisyPreferencesPrivate));
    object_class->dispose = whoopsie_daisy_preferences_dispose;
}

static void
on_privacy_policy_clicked (GtkWidget* button, gpointer user_data)
{
    system ("xdg-open " PRIVACY_URL);
}

static void
on_permission_changed (GPermission* permission, GParamSpec* pspec, gpointer data)
{
    gboolean allowed;
    GtkWidget* error_reports_box = NULL;
    WhoopsieDaisyPreferencesPrivate* priv = WHOOPSIE_DAISY_PREFERENCES (data)->priv;

    error_reports_box = GTK_WIDGET (gtk_builder_get_object (
                                    priv->builder, "error_reports_box"));

    allowed = g_permission_get_allowed (permission);
    gtk_widget_set_sensitive (error_reports_box, allowed);
}

static void
on_submit_error_reports_checked (GtkToggleButton* button, gpointer user_data)
{
    GError* error = NULL;

    whoopsie_preferences_call_set_report_crashes_sync (proxy,
        gtk_toggle_button_get_active (button), NULL, &error);
    if (error != NULL) {
        g_printerr ("Error setting crash reporting: %s\n", error->message);
        g_error_free (error);
    }
}

static void
on_properties_changed (WhoopsiePreferences* interface,
                       GVariant* changed_properties,
                       const gchar* const* invalidated_properties,
                       gpointer user_data)
{
    WhoopsieDaisyPreferencesPrivate* priv = WHOOPSIE_DAISY_PREFERENCES (user_data)->priv;
    gboolean report_errors;
    GtkWidget* submit_error_reports = NULL;

    submit_error_reports = GTK_WIDGET (
        gtk_builder_get_object (priv->builder, "submit_error_reports"));
    report_errors = whoopsie_preferences_get_report_crashes (interface);
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (submit_error_reports), report_errors);
}

static void
whoopsie_daisy_preferences_setup_dbus (WhoopsieDaisyPreferences *self, GError *error)
{
    WhoopsieDaisyPreferencesPrivate* priv = WHOOPSIE_DAISY_PREFERENCES (self)->priv;
    proxy = whoopsie_preferences_proxy_new_for_bus_sync (G_BUS_TYPE_SYSTEM,
                                         G_DBUS_PROXY_FLAGS_NONE,
                                         "com.ubuntu.WhoopsiePreferences",
                                         "/com/ubuntu/WhoopsiePreferences",
                                         NULL, &error);
    if (!proxy)
        return

    g_signal_connect (proxy, "g-properties-changed",
                                   G_CALLBACK (on_properties_changed), self);
    on_properties_changed (proxy, NULL, NULL, self);
}
static void
whoopsie_daisy_preferences_init (WhoopsieDaisyPreferences *self)
{
    GError *error = NULL;
    GtkWidget* privacy_page = NULL;
    GtkWidget* unlock_align = NULL;
    GtkWidget* unlock_button = NULL;
    GtkWidget* submit_error_reports = NULL;
    GtkWidget* privacy_policy = NULL;
    WhoopsieDaisyPreferencesPrivate* priv;
    priv = self->priv = WHOOPSIE_DAISY_PREFERENCES_PRIVATE (self);
    
    priv->builder = gtk_builder_new ();
    gtk_builder_set_translation_domain (priv->builder, GETTEXT_PACKAGE);
    gtk_builder_add_from_file(priv->builder, GNOMECC_UI_DIR "/whoopsie.ui", &error);
    if (error != NULL) {
        g_warning ("Could not load interface file: %s", error->message);
        g_error_free (error);
        return;
    }
    submit_error_reports = GTK_WIDGET (
        gtk_builder_get_object (priv->builder, "submit_error_reports"));
    privacy_page = GTK_WIDGET (
        gtk_builder_get_object (priv->builder, "privacy_page_box"));
    unlock_align = GTK_WIDGET (
        gtk_builder_get_object (priv->builder, "unlock_alignment"));
    privacy_policy = GTK_WIDGET (
        gtk_builder_get_object (priv->builder, "privacy_policy"));

    gtk_widget_reparent (privacy_page, (GtkWidget *) self);
    g_object_set (self, "valign", GTK_ALIGN_START, NULL);

    priv->permission = polkit_permission_new_sync (POL_PATH, NULL, NULL, &error);
    if (!priv->permission) {
        g_warning ("Could not acquire permission: %s", error->message);
        g_error_free (error);
    }

    unlock_button = gtk_lock_button_new (priv->permission);
    gtk_container_add (GTK_CONTAINER (unlock_align), GTK_WIDGET (unlock_button));
    gtk_widget_show (unlock_button);

    g_signal_connect (priv->permission, "notify", G_CALLBACK (on_permission_changed), self);
    on_permission_changed (priv->permission, NULL, self);

    whoopsie_daisy_preferences_setup_dbus (self, error);
    if (error) {
        g_warning ("Could not set up DBus connection: %s", error->message);
        g_error_free (error);
    }

    g_signal_connect (submit_error_reports, "toggled",
                      G_CALLBACK (on_submit_error_reports_checked), NULL);
    g_signal_connect (privacy_policy, "clicked",
                      G_CALLBACK (on_privacy_policy_clicked), NULL);
}

GtkWidget*
whoopsie_daisy_preferences_new (void)
{
    return g_object_new (WHOOPSIE_DAISY_TYPE_PREFERENCES, NULL);
}

