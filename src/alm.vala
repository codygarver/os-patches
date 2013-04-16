/*
 * Alm.vala
 * Copyright (C) 2012 Seif Lotfy <seif@lotfy.com>
 * Copyright (C) 2012 Intel Corp.
 *               Authored by: Seif Lotfy <seif.lotfy@collabora.co.uk>
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

using GLib;
using Gtk;


namespace Alm {
	public class Main : Gtk.Window 
	{
		public Main ()
		{
			this.set_title (_("Activity Log Manager"));
			var widget = new ActivityLogManager();
			this.add(widget);
			this.show_all();
			this.destroy.connect(on_destroy);
		}
		[CCode (instance_pos = -1)]
		public void on_destroy (Widget window) 
		{
			Gtk.main_quit();
		}
		static int main (string[] args) 
		{
			Gtk.init (ref args);
			var alm = new Gtk.Application ("org.zeitgeist.Alm", 
										ApplicationFlags.FLAGS_NONE);
			var window = new Main ();
			alm.add_window (window);
			
			Gtk.main ();
			return 0;
		}
	}
}
