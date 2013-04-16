/* -*- Mode: vala; tab-width: 4; intend-tabs-mode: t -*- */
/* alm
 *
 * Copyright (C) 2012 Seif Lotfy <seif@lotfy.com>
 * Copyright (C) 2012 Manish Sinha <manishsinha@ubuntu.com>
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

using Gtk;
using Gee;
using Zeitgeist;

namespace Alm {

	public class HistoryWidget : Gtk.Box {

		private ArrayList<string> past_records;
		private CalendarWidget calendar_box;
		private ButtonBox button_box;
		private Zeitgeist.Log zg_log;
		private Button del_button;
		ComboBoxText history_erase_kind;
		
		public HistoryWidget () {
			Object (orientation: Orientation.VERTICAL);
			this.spacing = 0;
			this.set_border_width(12);
			zg_log = new Zeitgeist.Log ();

			past_records = new ArrayList<string>();
			past_records.add(_("The past hour"));
			past_records.add(_("The past day"));
			past_records.add(_("The past week"));
			past_records.add(_("All"));
			past_records.add(_("Advanced"));

			this.set_up_ui ();
		}

		public void set_up_ui () {
			var top_box = new Box(Orientation.HORIZONTAL, 21);
			top_box.set_margin_top(9);
			this.pack_start(top_box, false, false);

			var text_box = new Box(orientation=Orientation.VERTICAL, 0);
			var header = new Label("");
			header.set_markup("<b>%s:</b>".printf(_("Forget activities")));
			header.set_alignment(0, (float)0.5);
			header.set_padding(0, 0);
			
			text_box.pack_start(header, false, false);

			var label = new Label(null);
			label.set_markup("<span size='small'>%s</span>".printf(_("Every time a file or an application is used, some information can be stored. This activity can be used to retrieve files during searches or as history in applications.")));
			label.set_line_wrap(true);
			label.set_line_wrap_mode(Pango.WrapMode.WORD);
			label.set_alignment(0, 0.5f);
			text_box.pack_start(label, false, false, 6);
			top_box.pack_start(text_box, false, false);

			history_erase_kind = new ComboBoxText();
			history_erase_kind.set_size_request(190, 0);
			for(int i = 0; i < this.past_records.size; i++)
			{
				history_erase_kind.append("", this.past_records[i]);
			}
			history_erase_kind.set_active (0);
			// Using anonymous function since using callback with 
			// on_history_combo_changed throws up a vala error:
			// Cannot convert from `Alm.HistoryWidget.on_history_combo_changed' to `Gtk.ComboBox.changed'
			history_erase_kind.changed.connect(() => {
				on_history_combo_changed(history_erase_kind);
			});
			var temp_box = new Box(orientation=Gtk.Orientation.VERTICAL, 0);
			temp_box.pack_start(new Gtk.Label(""), true, true, 0);
			temp_box.pack_start(history_erase_kind, true, true, 0);
			temp_box.pack_start(new Gtk.Label(""), true, true, 0);
			top_box.pack_end(temp_box, false, false, 0);
			
			//this.pack_start(this.calendar_box, false, false);
			//this.remove(this.calendar_box);

			this.button_box = new ButtonBox(Orientation.HORIZONTAL);
			this.button_box.layout_style = ButtonBoxStyle.START;
			this.pack_end(new Gtk.Box(Orientation.HORIZONTAL, 0), true, true);
			this.pack_end(this.button_box, false, false);

			this.del_button = new Button.from_stock(Stock.DELETE);
			del_button.set_label(_("Delete history"));
			
			// Create Calendar
			this.calendar_box = new CalendarWidget(del_button);
			

			//button_box.pack_start(label2, false, false);
			button_box.pack_start(history_erase_kind, false, false);
			button_box.pack_start(del_button, false, false);
			del_button.clicked.connect(()=> {
				Zeitgeist.TimeRange tr;
				var index = this.history_erase_kind.get_active();
				if (index < 3) {
					int range = 60*60*1000;
					if (index == 0)
						range = 1 * range;
					else if (index == 1)
						range = range*24;
					else if (index == 2)
						range = range * 24 * 7;
					int64 end = Zeitgeist.Timestamp.now ();
					int64 start = end - range;
					tr = new Zeitgeist.TimeRange (start, end);
					get_history.begin (tr);
				}
				else if (index == 3){
					tr = new Zeitgeist.TimeRange.anytime();
					get_history.begin (tr);
				}
				else if (index == 4){
					tr = this.calendar_box.get_range();
					get_history.begin (tr);
				}
			});
		}

		private async void get_history(TimeRange tr) {
			Idle.add (get_history.callback, Priority.LOW);
			yield;
			
			var dialog = new Gtk.Dialog();
			dialog.add_button(Stock.CANCEL, ResponseType.CANCEL);
			dialog.add_button(Stock.YES, ResponseType.OK);
			dialog.set_title("");
			
			var label = new Gtk.Label(_("This operation cannot be undone, are you sure you want to delete this activity?"));
			label.set_line_wrap(true);
			label.set_line_wrap_mode(Pango.WrapMode.WORD);
			label.set_padding(9,9);
			((Gtk.Container) dialog.get_content_area ()).add(label);
			
			dialog.set_transient_for((Gtk.Window)this.get_toplevel());
			dialog.set_modal(true);
			dialog.show_all();
			int res = dialog.run();
			dialog.destroy();
			
			if(res == ResponseType.OK) {
				var ptr_arr = new PtrArray ();
				ptr_arr.add (new Zeitgeist.Event ());
				try {
					Array<int> ids = yield zg_log.find_event_ids (tr, (owned) ptr_arr,
							Zeitgeist.StorageState.ANY, 0, 0, null);
					delete_history.begin(ids);
				}
				catch (Error err) {
					warning ("%s", err.message);
				}
			}
			
			
			
		}

		private async void delete_history (Array<int>? ids) {
			Idle.add (delete_history.callback, Priority.LOW);
			yield;
			try {
				bool rs = yield zg_log.delete_events(ids, null);
			}
			catch (Error err) {
				warning ("%s", err.message);
			}
		}

		private void insert_calendar () {
			//this.remove(this.button_box);
			//debug("Inserting calendar instance");
			//this.pack_end(this.calendar_box, false, false);
			//this.pack_start(this.button_box, false, false);
			if (this.calendar_box.get_parent() == null)
				this.pack_start(this.calendar_box, false, false, 9);
			this.calendar_box.show_all();
		}

		private void remove_calendar () {
			//debug("Removing calendar instance");
			//this.remove(this.calendar_box);
			this.calendar_box.hide();
		}

		private void on_history_combo_changed (ComboBoxText box) {
			if(box.get_active() == 4)
			{
				//debug("Inserting calendar");
				var x = calendar_box.get_range();
				this.insert_calendar();
			}
			else
			{
				//debug("Removing calendar");
				del_button.set_sensitive(true);
				this.remove_calendar();
			}
		}
	}
	
	public class CalendarDialog : Gtk.Dialog {
		private Calendar calendar;
		public CalendarDialog () {
			Object();
			this.calendar = new Calendar();
			((Gtk.Container) this.get_content_area ()).add(this.calendar);
			this.set_decorated(false);
			this.set_position(0);
			this.set_property("skip-taskbar-hint", true);
		}
		public Calendar get_calendar_widget () {
			return calendar;
		}
	
	}
	
	public class CalendarWidget : Gtk.Grid {
		
		private Entry start_entry;
		private Entry end_entry;
		private CalendarDialog start_dialog;
		private CalendarDialog end_dialog;
		private Gtk.Button button;
		private Label invalid_label;
		
		public CalendarWidget (Gtk.Button button) {
			Object ();
			
			this.button = button;
			start_dialog = new CalendarDialog();
			end_dialog = new CalendarDialog();
			
			this.set_row_spacing(10);
			this.set_column_spacing(15);
			
			var box1 = new Box(Orientation.HORIZONTAL, 0);
			start_entry = new Entry();
			var start_button = new Button();
			var arrow1 = new Arrow(Gtk.ArrowType.DOWN, 0);
			start_button.add(arrow1);
			start_entry.set_editable(false);
			start_entry.set_size_request(100, -1);
			box1.pack_start(start_entry, true, true, 0);
			box1.pack_start(start_button, true, true, 0);
			start_button.clicked.connect(() => {
				on_clicked (start_button, start_entry, start_dialog);
				});
			
			var box2 = new Box(Orientation.HORIZONTAL, 0);
			end_entry = new Entry();
			var end_button = new Button();
			var arrow2 = new Arrow(Gtk.ArrowType.DOWN, 0);
			end_button.add(arrow2);
			end_entry.set_editable(false);
			end_entry.set_size_request(100, -1);
			box2.pack_start(end_entry, true, true, 0);
			box2.pack_start(end_button, true, true, 0);
			end_button.clicked.connect(() => {
				on_clicked (end_button, end_entry, end_dialog);
				});
			
			//this.pack_start(label_box, true, true, 0);
			//this.pack_start(combo_box_box, false, false, 9);
			
			var start_label = new Label("");
			start_label.set_markup(_("From:"));
			start_label.set_alignment(1, 0/5);
			
			var end_label = new Label("");
			end_label.set_markup(_("To:"));
			end_label.set_alignment(1, 0/5);
			
			//combo_box_box.pack_start(start_entry, true, true, 0);
			//combo_box_box.pack_start(end_entry, true, true, 0);
			this.add(start_label);
			this.attach(box1, 1, 0, 1, 1);
			this.attach(end_label, 0, 1, 1, 1);
			this.attach(box2, 1, 1, 1, 1);
			
			this.invalid_label = new Gtk.Label("");
			invalid_label.set_markup("<span color='red'><b>%s</b></span>".printf(_("Invalid Timerange")));
			
			this.set_up_calendar(start_button, start_entry, start_dialog);
			this.set_up_calendar(end_button, end_entry, end_dialog);
			
			this.show_all();
		}
		
		public TimeRange get_range() {
			var calendar = start_dialog.get_calendar_widget();
			uint year;
			uint month;
			uint day;
			calendar.get_date(out year, out month, out day);
			DateTime date = new DateTime.local((int)year, (int)month+1, (int)day, 0, 0 ,0);
			var start = date.to_unix()*1000;
			
			calendar = end_dialog.get_calendar_widget();
			calendar.get_date(out year, out month, out day);
			date = new DateTime.local((int)year, (int)month+1, (int)day, 0, 0 ,0);
			var end = date.to_unix()*1000;
				
			
			//
			if (start > end) {
				this.button.set_sensitive(false);
				if (this.invalid_label.get_parent() == null)
					this.attach(this.invalid_label, 2, 0, 1, 2);
				this.invalid_label.show();
			}
			else {
				this.button.set_sensitive(true);
				this.invalid_label.hide();
			}
			
			return new TimeRange(start, end);
		}
		
		public void set_up_calendar(Button widget, Entry entry, CalendarDialog dialog) {
			var calendar = dialog.get_calendar_widget();
			uint year;
			uint month;
			uint day;
			calendar.get_date(out year, out month, out day);
		
			DateTime date = new DateTime.local((int)year, (int)month+1, (int)day, 0, 0 ,0);
			var date_string = date.format(_("%d %B %Y"));
			entry.set_text(date_string);
			widget.set_sensitive(true);
			dialog.hide();
		}
		
		public void on_clicked(Widget widget, Entry entry, CalendarDialog dialog) {
			dialog.show_all();
			var parent_window = this.get_parent_window();
			int window_x;
			int window_y;
			parent_window.get_position(out window_x, out window_y);
			Allocation allocation;
			entry.get_allocation(out allocation);
			dialog.move(window_x + allocation.x,
				window_y + allocation.y + allocation.height);
			dialog.set_size_request(allocation.width, -1);
			dialog.resizable = false;
			widget.set_sensitive(false);
			dialog.focus_out_event.connect_after((w, e) => {
				dialog.hide();
				widget.set_sensitive(true);
				return false;
			});
			var cal = dialog.get_calendar_widget();
			cal.day_selected_double_click.connect(() => {
				var calendar = dialog.get_calendar_widget();
				uint year;
				uint month;
				uint day;
				calendar.get_date(out year, out month, out day);
				
				DateTime date = new DateTime.local((int)year, (int)month+1, (int)day, 0, 0 ,0);
				var date_string = date.format(_("%d %B %Y"));
				entry.set_text(date_string);
				widget.set_sensitive(true);
				dialog.hide();
				var range = get_range();
			});
		}
	}
}
