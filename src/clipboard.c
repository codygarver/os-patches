/*
 * src/clipboard.c - X clipboard hack to detect if daemon is running
 *
 * Elliot Lee <sopwith@redhat.com>
 *
 * (C) Copyright 1999 Red Hat, Inc.
 *
 * Licensed under the GNU GPL v2.  See COPYING.
 */

#include "config.h"

#include <gdk/gdkx.h>

#include "update-notifier.h"

/*
 * clipboard_get_func - dummy get_func for gtk_clipboard_set_with_data ()
 */
static void
clipboard_get_func (GtkClipboard *clipboard __attribute__((__unused__)),
		   GtkSelectionData *selection_data __attribute__((__unused__)),
		    guint info __attribute__((__unused__)),
		    gpointer user_data_or_owner __attribute__((__unused__)))
{
}

/*
 * clipboard_clear_func - dummy clear_func for gtk_clipboard_set_with_data ()
 */
static void
clipboard_clear_func (GtkClipboard *clipboard __attribute__((__unused__)),
		      gpointer user_data_or_owner __attribute__((__unused__)))
{
}

/*
 * up_get_clipboard - try and get the CLIPBOARD_NAME clipboard
 *
 * Returns TRUE if successfully retrieved and FALSE otherwise.
 */
gboolean
up_get_clipboard (void)
{
	static const GtkTargetEntry targets[] = { {CLIPBOARD_NAME, 0, 0} };
	gboolean retval = FALSE;
	GtkClipboard *clipboard;
	Atom atom;
	Display *display;

	atom = gdk_x11_get_xatom_by_name (CLIPBOARD_NAME);
	display = gdk_x11_display_get_xdisplay (gdk_display_get_default ());

	XGrabServer (display);

	if (XGetSelectionOwner (display, atom) != None)
		goto out;

	clipboard = gtk_clipboard_get (gdk_atom_intern (CLIPBOARD_NAME, FALSE));

	if (gtk_clipboard_set_with_data (clipboard, targets,
					 G_N_ELEMENTS (targets),
					 clipboard_get_func,
					 clipboard_clear_func, NULL))
		retval = TRUE;

out:
	XUngrabServer (display);
	gdk_flush ();

	return retval;
}
