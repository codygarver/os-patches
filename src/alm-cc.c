/*
 * alm-cc.c
 * Copyright (C) Manish Sinha 2012 <manishsinha@ubuntu.com>
 * 
alm is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published
 * by the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 * 
 * alm is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.";
 */

#include "config.h"
#include <glib/gi18n-lib.h>
#include <gtk/gtk.h>
#include <libgnome-control-center/cc-panel.h>

extern void* alm_activity_log_manager_new (void);
#ifdef HAVE_WHOOPSIE
extern void alm_activity_log_manager_append_page (void* alm, GtkWidget* widget, const gchar* label);
extern void* whoopsie_daisy_preferences_new (void);
#endif

#define ALM_TYPE_MAIN_WINDOW_PANEL alm_main_window_panel_get_type()

typedef struct _AlmMainWindowPanel AlmMainWindowPanel;
typedef struct _AlmMainWindowPanelClass AlmMainWindowPanelClass;

struct _AlmMainWindowPanel
{
  CcPanel parent;
};

struct _AlmMainWindowPanelClass
{
  CcPanelClass parent_class;
};

G_DEFINE_DYNAMIC_TYPE (AlmMainWindowPanel, alm_main_window_panel, CC_TYPE_PANEL)

static void
alm_main_window_panel_class_finalize (AlmMainWindowPanelClass *klass)
{
}

static void
alm_main_window_panel_class_init (AlmMainWindowPanelClass *klass)
{
}

static void
alm_main_window_panel_init (AlmMainWindowPanel *self)
{
  GtkWidget *widget = GTK_WIDGET (alm_activity_log_manager_new ());
#ifdef HAVE_WHOOPSIE
  GtkWidget *whoopsie = GTK_WIDGET (whoopsie_daisy_preferences_new ());
  alm_activity_log_manager_append_page (widget, whoopsie, _("Diagnostics"));
#endif
  gtk_widget_show_all (widget);
  gtk_container_add (GTK_CONTAINER (self), widget);
}

static gboolean
delayed_init ()
{
	return FALSE;
}

void
g_io_module_load (GIOModule *module)
{

  bindtextdomain (GETTEXT_PACKAGE, LOCALE_DIR);
  bind_textdomain_codeset (GETTEXT_PACKAGE, "UTF-8");

  GtkIconTheme *theme = gtk_icon_theme_get_default ();
  gtk_icon_theme_append_search_path (theme, THEME_DIR);

  alm_main_window_panel_register_type (G_TYPE_MODULE (module));
  g_io_extension_point_implement (CC_SHELL_PANEL_EXTENSION_POINT,
                                  ALM_TYPE_MAIN_WINDOW_PANEL,
                                  "activity-log-manager", 0);

  g_idle_add(delayed_init, NULL);
}

void
g_io_module_unload (GIOModule *module)
{
}
