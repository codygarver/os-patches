
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include <glib.h>
#include <glib-object.h>
#include <gtk/gtk.h>

#include <sys/types.h>
#include <sys/wait.h>

#include "update-notifier.h"
#include "cdroms.h"

#define CDROM_CHECKER PACKAGE_LIB_DIR"/update-notifier/apt-cdrom-check"

/* responses for the dialog */
enum {
   RES_START_PM=1,
   RES_DIST_UPGRADER=2,
   RES_APTONCD=3
};

/* Returnvalues from apt-cdrom-check:
    # 0 - no ubuntu CD
    # 1 - CD with packages
    # 2 - dist-upgrader CD
    # 3 - aptoncd media
*/
enum {
   NO_CD,
   CD_WITH_PACKAGES,
   CD_WITH_DISTUPGRADER,
   CD_WITH_APTONCD
};

static void
distro_cd_detected(int cdtype,
                   const char *mount_point)
{
   GtkWidget *dialog = gtk_message_dialog_new(NULL, GTK_DIALOG_MODAL,
					      GTK_MESSAGE_QUESTION, 
					      GTK_BUTTONS_NONE,
					      NULL );
   gchar *title, *markup;
   switch(cdtype) {
   case CD_WITH_PACKAGES:
      title = _("Software Packages Volume Detected");
      markup = _("<span weight=\"bold\" size=\"larger\">"
	    "A volume with software packages has "
	    "been detected.</span>\n\n"
	    "Would you like to open it with the "
	    "package manager?");
      gtk_dialog_add_buttons(GTK_DIALOG(dialog), 
			     GTK_STOCK_CANCEL,
			     GTK_RESPONSE_REJECT,
			     _("Start Package Manager"), 
			     RES_START_PM,
			     NULL);
      gtk_dialog_set_default_response (GTK_DIALOG(dialog), RES_START_PM);
      break;
   case CD_WITH_DISTUPGRADER:
      title = _("Upgrade volume detected");
      markup = _("<span weight=\"bold\" size=\"larger\">"
	    "A distribution volume with software packages has "
	    "been detected.</span>\n\n"
	    "Would you like to try to upgrade from it automatically? ");
      gtk_dialog_add_buttons(GTK_DIALOG(dialog), 
			     GTK_STOCK_CANCEL,
			     GTK_RESPONSE_REJECT,
			     _("Run upgrade"), 
			     RES_DIST_UPGRADER,
			     NULL);
      gtk_dialog_set_default_response (GTK_DIALOG(dialog), RES_DIST_UPGRADER);
      break;
#if 0  //  we don't have aptoncd support currently, g-a-i is not
       // in the archive anymore
   case CD_WITH_APTONCD:
      title = _("APTonCD volume detected");
      markup = _("<span weight=\"bold\" size=\"larger\">"
	    "A volume with unofficial software packages has "
	    "been detected.</span>\n\n"
	    "Would you like to open it with the "
	    "package manager?");
      gtk_dialog_add_buttons(GTK_DIALOG(dialog), 
			     GTK_STOCK_CANCEL,
			     GTK_RESPONSE_REJECT,
			     _("Start package manager"), 
			     RES_START_PM,
			     NULL);
      gtk_dialog_set_default_response (GTK_DIALOG(dialog), RES_START_PM);
      break;      
#endif
   default:
      g_assert_not_reached();
   }

   gtk_window_set_title(GTK_WINDOW(dialog), title);
   gtk_window_set_skip_taskbar_hint (GTK_WINDOW(dialog), FALSE);
   gtk_message_dialog_set_markup(GTK_MESSAGE_DIALOG(dialog), markup);

   int res = gtk_dialog_run (GTK_DIALOG (dialog));
   switch(res) {
   gchar *argv[5];
   case RES_START_PM:
      argv[0] = "/usr/lib/update-notifier/backend_helper.py";
      argv[1] = "add_cdrom";
      argv[2] = (gchar *)mount_point;
      argv[3] = NULL;
      g_spawn_async (NULL, argv, NULL, 0, NULL, NULL, NULL, NULL);
      break;
   case RES_DIST_UPGRADER:
      argv[0] = "/usr/bin/pkexec";
      argv[1] = "/usr/lib/update-notifier/cddistupgrader";
      argv[2] = (gchar *)mount_point;
      argv[3] = NULL;
      g_spawn_async (NULL, argv, NULL, 0, NULL, NULL, NULL, NULL);
      break;
   default:
      /* do nothing */
      break;
   }
   gtk_widget_destroy (dialog);
}

int
main (int argc, char **argv)
{
    if ( argc != 3 )
    {
        printf("usage: %s cdtype mountpoint", argv[0]);
        return 1;
    }
    else
    {
        int cdtype = atoi(argv[1]);
        char *mount_point = argv[2];
        if(cdtype > 0) {
            gtk_init (&argc, &argv);
            distro_cd_detected(cdtype, mount_point);
            return 0;
        }
    }
}
