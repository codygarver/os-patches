#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include <glib.h>
#include <glib-object.h>
#include <gtk/gtk.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <glib/gi18n.h>

#include "update-notifier.h"
#include "system-crash.h"

static gboolean
ask_invoke_apport_with_pkexec(void)
{
   GtkDialog *dialog;
   gchar *msg = _("System program problem detected");
   gchar *descr = _("Do you want to report the problem "
                    "now?");
   dialog = (GtkDialog*)gtk_message_dialog_new (NULL,
                                    GTK_DIALOG_DESTROY_WITH_PARENT,
                                    GTK_MESSAGE_QUESTION,
                                    GTK_BUTTONS_NONE,
                                    "%s", msg);
   gtk_message_dialog_format_secondary_text(GTK_MESSAGE_DIALOG(dialog),
                                            "%s", descr);
   gtk_dialog_add_button(dialog, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL);
   gtk_dialog_add_button(dialog, _("Report problem…"), GTK_RESPONSE_ACCEPT);
   int res = gtk_dialog_run(dialog);
   gtk_widget_destroy(GTK_WIDGET(dialog));
   if (res == GTK_RESPONSE_ACCEPT)
      return TRUE;
   return FALSE;
}

void
invoke_with_pkexec(const gchar *cmd)
{
        g_debug("invoke_with_pkexec ()");
        gchar *argv[3];
        argv[0] = "/usr/bin/pkexec";
        argv[1] = (gchar*)cmd;
        argv[2] = NULL;
        g_spawn_async (NULL, argv, NULL, G_SPAWN_DO_NOT_REAP_CHILD, NULL, NULL, NULL, NULL);
}

int
main (int argc, char **argv)
{
   gtk_init (&argc, &argv);
   // be nice and always ask first before firing up pkexec
   if (ask_invoke_apport_with_pkexec()) {
      invoke_with_pkexec(CRASHREPORT_REPORT_APP);
   } else {
      return g_spawn_command_line_async(CRASHREPORT_REPORT_APP, NULL);
   }
   return 0;
}
