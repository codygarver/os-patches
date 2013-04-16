/*
 * activity-log-manager.vala
 * Copyright (C) 2012 Seif Lotfy <seif@lotfy.com>
 * Copyright (C) 2012 Stefano Candori <stefano.candori@gmail.com>
 * Copyright (C) 2012 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright (C) 2012 Intel Corp.
 *               Authored by: Seif Lotfy <seif.lotfy@collabora.co.uk>
 * 
 * alm is free software: you can redistribute it and/or modify it
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
namespace Alm {
	public class ActivityLogManager : Gtk.Box {
		private Gtk.Notebook notebook;
		private HistoryWidget history_widget;
		private FilesWidget files_widget;
		private ApplicationsWidget apps_widget;

		private Blacklist blacklist;
		private Gtk.Switch logging_switch;

		public ActivityLogManager () {
			Object(orientation: Gtk.Orientation.VERTICAL);
			this.set_size_request(600, 450);
			this.spacing = 6;

			this.margin = 12;

			blacklist = new Blacklist();
			notebook = new Gtk.Notebook();

			this.pack_start(notebook, true, true, 0);

			history_widget = new HistoryWidget();
			var history_label = new Gtk.Label(_("Recent Items"));
			notebook.append_page(history_widget, history_label);
			
			
			files_widget = new FilesWidget(blacklist);
			var files_label = new Gtk.Label(_("Files"));
			notebook.append_page(files_widget, files_label);
			
			apps_widget = new ApplicationsWidget(blacklist);
			var app_label = new Gtk.Label(_("Applications"));
			notebook.append_page(apps_widget, app_label);
			
			var logging_box = new Gtk.Box(Gtk.Orientation.HORIZONTAL, 6);
			logging_box.margin_right = 12;

			var logging_label = new Gtk.Label(null);
			logging_label.set_markup("<b>%s</b>".printf(_("Record Activity")));

			logging_switch = new Gtk.Switch();
			logging_box.pack_end(logging_switch, false, false);
			logging_box.pack_end(logging_label, false, false);
			logging_switch.set_active(!blacklist.get_incognito());
			blacklist.incognito_toggled.connect(on_incognito_toggled);

			logging_switch.notify["active"].connect(on_switch_activated);

			this.pack_start(logging_box, false, false, 9);
		
			this.show_all();
		}

        public void append_page (Gtk.Widget widget, string label) {
			var app_label = new Gtk.Label(_(label));
			notebook.append_page(widget, app_label);
        }
		public void on_incognito_toggled(bool status) {
			this.logging_switch.set_active(!status);
		}
		
		public void on_switch_activated() {
			var recording = !blacklist.get_incognito();
			if (this.logging_switch.get_active() != recording) {
				blacklist.set_incognito(recording);
			}
		}
	}
}
