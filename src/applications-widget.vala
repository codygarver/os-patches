/* -*- Mode: vala; tab-width: 4; intend-tabs-mode: t -*- */
/* alm
 *
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
 
using Gtk;
using Gee;
using GLib;
using Zeitgeist;

namespace Alm {

	public class ApplicationsWidget : Gtk.Box {

		private Blacklist blacklist_interface;

		private ApplicationBlacklist app_blacklist;
		private ApplicationsChooserDialog app_dialog;
		private ApplicationsTreeView app_treeview;
		private Gtk.Box container_box;

		private HashTable<string, AppChooseInfo> blocked_list;
		private HashTable<string, AppChooseInfo> unblocked_list;

		private bool app_change_recursive;

		public ApplicationsWidget (Blacklist blacklist_inter) {
			Object (orientation: Orientation.VERTICAL);
			
			this.blacklist_interface = blacklist_inter;
			this.blocked_list = new HashTable<string, AppChooseInfo>(str_hash, str_equal);
			this.unblocked_list = new HashTable<string, AppChooseInfo>(str_hash, str_equal);

			this.app_blacklist = new ApplicationBlacklist (this.blacklist_interface);
			this.app_treeview = new ApplicationsTreeView(app_blacklist, blocked_list, unblocked_list);
			this.set_up_ui ();
		}

		private void set_up_ui () {
			this.set_spacing(6);
			this.set_border_width (12);

			container_box = new Gtk.Box(Orientation.VERTICAL, 0);


			this.app_blacklist.application_removed.connect((app, event) => {
				if(!app_change_recursive)
					this.app_treeview.remove_app_from_view(app);
				app_change_recursive = false;
			});
			this.app_blacklist.application_added.connect((app, event) => {
				if(!app_change_recursive)
					this.app_treeview.add_application_to_view(app);
				app_change_recursive = false;
			});

			app_treeview.visible = true;
			var app_toolbar = new Toolbar();
			app_toolbar.toolbar_style = ToolbarStyle.ICONS;
			app_toolbar.icon_size = 1;
			app_toolbar.icon_size_set = true;
			app_toolbar.visible = true;
			
			//scroll.get_style_context().set_junction_sides(Gtk.JunctionSides.BOTTOM);
    		app_toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR);
		    app_toolbar.get_style_context().set_junction_sides(Gtk.JunctionSides.TOP);

			var app_add = new ToolButton(null, _("Add Application"));
			app_add.set_icon_name("list-add-symbolic");
			app_add.clicked.connect(app_add_clicked);

			var app_remove = new ToolButton(null, _("Remove Application"));
			app_remove.set_icon_name("list-remove-symbolic");
			app_remove.clicked.connect(app_remove_clicked);

			app_toolbar.insert(app_add, 0);
			app_toolbar.insert(app_remove, 1);

			container_box.pack_start(app_treeview, true, true);
			container_box.pack_start(app_toolbar, false, false);

			var label = new Label(null);
			label.set_markup("<b>%s</b>".printf(_("Do not log activity from the following applications:")));
			label.set_alignment(0, 0.5f);
			
			this.pack_start(label, false, false);
			this.pack_start(container_box, true, true);

			var app_list = this.app_blacklist.all_apps;

			// Fetch all the blocked apps
			this.populate_view(app_list);

			// Fetch all the applications for populating the app chooser box
			this.app_dialog = new ApplicationsChooserDialog (this.app_blacklist, blocked_list, unblocked_list);
		}

		public void app_add_clicked(ToolButton button) {
			this.app_dialog.set_transient_for((Gtk.Window)this.get_toplevel());
			this.get_toplevel().set_sensitive(false);
			this.app_dialog.set_modal(true);
			app_dialog.set_title(_("Select Application"));
			//FIXME: use proper modality
			int res = this.app_dialog.run();
			this.get_toplevel().set_sensitive(true);
			if(res == ResponseType.OK) {
				TreeSelection sel = this.app_dialog.tree.get_selection ();
				TreeModel model;
				TreeIter iter;
				sel.get_selected(out model, out iter);
				string app;
				model.get(iter, 2, out app);
				this.app_dialog.liststore.remove(iter);

				// Add the App to View
				app_change_recursive = true;
				this.app_treeview.add_application_to_view(app);
				this.app_blacklist.block(app);

				AppChooseInfo info = unblocked_list.lookup(app);
				if(info != null)
				{
					unblocked_list.remove(app);
					if(blocked_list.lookup(app) == null)
						blocked_list.insert(app, info);
					else
						blocked_list.replace(app, info);
				}
			}
			this.app_dialog.hide();			
		}

		public void app_remove_clicked(ToolButton button) {
			// Remove the selected app from the view
			var app = this.app_treeview.remove_selected_app();
			if(app != null)
			{
				app_change_recursive = true;
				this.app_blacklist.unblock(app);
			
				AppChooseInfo info = blocked_list.lookup(app);
				if(info != null)
				{
					blocked_list.remove(app);
					if(unblocked_list.lookup(app) == null)
						unblocked_list.insert(app, info);
					else
						unblocked_list.replace(app, info);
				}
				this.app_dialog.insert_app_liststore(app);
			}
		}

		private void populate_view(HashSet<string> app_list) {
			foreach(string app in app_list)
				this.app_treeview.add_application_to_view(app);
		}

		public static string markup_for_app(DesktopAppInfo app_info) {
			var app_name = app_info.get_name ();
			var description = app_info.get_description();
			description = description != null? description: _("No description available");

			return "<b>%s</b>\n%s".printf(GLib.Markup.escape_text(app_name), 
					GLib.Markup.escape_text(description));
		}
	}

	public class ApplicationBlacklist { //: remote.GenericBlacklist
		private Blacklist blacklist_interface;
		
		public static string interpretation_prefix = "app-";
		
		public static string launcher_prefix = "launch-";

		private HashSet<string> all_blocked_apps;

		public signal void application_added(string app, Event ev);

		public signal void application_removed(string app, Event ev);

		public ApplicationBlacklist (Blacklist blacklist) {
			this.blacklist_interface = blacklist;
			this.blacklist_interface.template_added.connect(on_blacklist_added);
			this.blacklist_interface.template_removed.connect(on_blacklist_removed);

			this.get_blocked_apps();
			
		}

		public void get_all_applications(ApplicationsChooserDialog dialog) {
			this.blacklist_interface.get_all_applications(dialog);
		}

		public HashSet<string> all_apps {
			get {
				return all_blocked_apps;
			}
		}

		public void get_count_for_app(string id, TreeIter iter, ListStore store) {
			this.blacklist_interface.get_count_for_app(id, iter, store);
		}

		private HashSet<string> get_blocked_apps() {
			all_blocked_apps = new HashSet<string>();

			foreach(string key in blacklist_interface.all_templates.get_keys()) {
				if(key.has_prefix(interpretation_prefix))
				{
					var app = key.substring(4);
					all_blocked_apps.add(app);
				}
			}
			
			return all_blocked_apps;
		}

		private void on_blacklist_added (string blacklist_id, Event ev) {
			if(blacklist_id.has_prefix(interpretation_prefix))
			{
				string app = blacklist_id.substring(4);
				application_added(app, ev);
				if(!all_apps.contains(app))
					all_apps.add(app);
			}
		}

		private void on_blacklist_removed (string blacklist_id, Event ev) {
			if(blacklist_id.has_prefix(interpretation_prefix))
			{
				string app = blacklist_id.substring(4);
				application_removed(app, ev);
				if(all_apps.contains(app))
					all_apps.remove(app);
			}
		}

		public void block(string application) {
			Event ev = new Event();
			ev.set_actor("application://%s".printf(application));
			Subject sub = new Subject();			
			ev.add_subject(sub);

			Event launch_ev = new Event();
			Subject launch_sub = new Subject();
			launch_sub.set_uri("application://%s".printf(application));
			launch_ev.add_subject(launch_sub);
			
			blacklist_interface.add_template(
					"%s%s".printf(interpretation_prefix, application), ev);
			blacklist_interface.add_template(
					"%s%s".printf(launcher_prefix, application), launch_ev);
			if(!all_apps.contains(application))
					all_apps.add(application);
		}

		public void unblock(string application) {
			blacklist_interface.remove_template(
					"%s%s".printf(interpretation_prefix, application));
			blacklist_interface.remove_template(
					"%s%s".printf(launcher_prefix, application));

			if(all_apps.contains(application))
				all_apps.remove(application);
		}
	}

	private class ApplicationsTreeView : Gtk.Box {
	
		private ApplicationBlacklist app_blacklist;
		private ListStore store;
		private TreeView treeview;
		
		HashTable<string, AppChooseInfo> blocked_apps;
		HashTable<string, AppChooseInfo> unblocked_apps;
		
		enum TreeViewCols
		{
			APP_NAME,
			ICON,
			DESKTOP_FILE,
			N_COLS
		}

		public ListStore liststore {
			get {
				return this.store;
			}
		}

		public ApplicationsTreeView (ApplicationBlacklist app_blacklist,
							HashTable<string, AppChooseInfo> blocked, 
								HashTable<string, AppChooseInfo> unblocked) {
			Object (orientation: Orientation.VERTICAL);
			
			this.app_blacklist = app_blacklist;
			this.blocked_apps = blocked;
			this.unblocked_apps = unblocked;

			this.store = new ListStore (TreeViewCols.N_COLS,
										typeof (string),
										typeof (Gdk.Pixbuf),
										typeof (string));
			this.treeview = new TreeView.with_model (this.store);
			this.treeview.set_headers_visible (false);
			this.treeview.set_rules_hint (true);
			this.set_up_ui ();
		}
		
		private void set_up_ui () {
			var column_pix_name = new TreeViewColumn ();
			column_pix_name.set_title (_("Name"));
			this.treeview.append_column (column_pix_name);
			var pix_rend = new CellRendererPixbuf ();
			column_pix_name.pack_start (pix_rend, false);
			column_pix_name.add_attribute (pix_rend, "pixbuf", 1);
			var name_rend = new CellRendererText ();
			name_rend.set_property ("ellipsize", Pango.EllipsizeMode.END);
			column_pix_name.pack_start (name_rend, true);
			column_pix_name.add_attribute (name_rend, "markup", 0);
			column_pix_name.set_resizable (true);
			
			var scroll = new ScrolledWindow (null, null);
			scroll.add (this.treeview);
			scroll.set_policy (PolicyType.NEVER, PolicyType.AUTOMATIC);
			scroll.set_shadow_type (ShadowType.IN);
			scroll.set_border_width (1);
			this.pack_start (scroll);
		}
		
		public static Gdk.Pixbuf? get_pixbuf_from_gio_icon (Icon? icon, int size=32) {
			Gdk.Pixbuf? pix = null;
			IconTheme theme = IconTheme.get_default ();
			IconInfo icon_info = null;
			/*If the application hasn't an icon in the current theme
			  let's use the gtk-execute icon: 
			  http://developer.gnome.org/gtk3/3.2/gtk3-Stock-Items.html#GTK-STOCK-EXECUTE:CAPS
			*/
			if(icon == null) {
				icon_info = theme.lookup_icon ("gtk-execute" ,
												size,
												IconLookupFlags.FORCE_SVG);
			}
			else {
				icon_info = theme.lookup_by_gicon (icon ,
													size,
													IconLookupFlags.FORCE_SVG);
				if (icon_info == null)
					icon_info = theme.lookup_icon ("gtk-execute" ,
												size,
												IconLookupFlags.FORCE_SVG);
			}
			try {
				pix = icon_info.load_icon ();
			}
			catch (Error e){
				return null;
			}
			return pix;
		}

		public void add_application_to_view(string app) {
			DesktopAppInfo app_info = new DesktopAppInfo(app);
			if (app_info != null ) {
				var pix = ApplicationsTreeView.get_pixbuf_from_gio_icon(app_info.get_icon());
				var markup = ApplicationsWidget.markup_for_app(app_info);
				TreeIter iter;
				this.liststore.append(out iter);
				this.liststore.set(iter, 0, markup, 1, pix, 2, app, -1);

				// Insert only when it is empty
				if(this.blocked_apps.lookup(app) == null)
					this.blocked_apps.insert(app, new AppChooseInfo(
														app_info.get_id(),
														app_info.get_name(),
														pix,
														"",
														0,
														0));
			}
		}
		
		public void remove_app_from_view (string app) {
			var model = this.treeview.get_model ();
			TreeIter iter;
			model.get_iter_first (out iter);
			while (true)
			{
				Value can_app_value;
				model.get_value(iter, 2, out can_app_value);
				string can_app = can_app_value.get_string();
				if(app == can_app)
				{
					this.store.remove(iter);
					break;
				}
				bool more_entires = model.iter_next(ref iter);
				if(!more_entires)
				{
					break;
				}
			}
		}
		
		public string? remove_selected_app() {
			var selection = this.treeview.get_selection();
			TreeModel model;
			TreeIter iter;
			string app = null;
			if(selection.get_selected(out model, out iter))
			{
				model.get(iter, 2, out app);
				this.liststore.remove(iter);
			}

			return app;
		}
	}

	private class AppSelectionTreeView : Gtk.Box {

		private ApplicationBlacklist app_blacklist;
		private ListStore store;
		private TreeView treeview;
		
		enum TreeViewCols
		{
			APP_NAME,
			ICON,
			DESKTOP_FILE,
			LAST_ACCESSED_STRING,
			LAST_ACCESSED_INT,
			USAGE,
			N_COLS
		}

		public TreeView tree {
			get {
				return treeview;
			}
		}

		public ListStore liststore {
			get {
				return store;
			}
		}

		public AppSelectionTreeView (ApplicationBlacklist app_blacklist) {
			Object (orientation: Orientation.VERTICAL);
			
			this.app_blacklist = app_blacklist;
			
			this.store = new ListStore (TreeViewCols.N_COLS,
										typeof (string),
										typeof (Gdk.Pixbuf),
										typeof (string),
										typeof (string),
										typeof (int64),
										typeof (uint));
			this.treeview = new TreeView.with_model (this.store);
			this.treeview.set_headers_visible (true);
			this.treeview.set_rules_hint (true);
			//this.treeview.set_fixed_height_mode (true);
			this.set_up_ui ();
		}
		
		private void set_up_ui () {
			var column_pix_name = new TreeViewColumn ();
			column_pix_name.set_title (_("Name"));
			this.treeview.append_column (column_pix_name);
			var pix_rend = new CellRendererPixbuf ();
			column_pix_name.pack_start (pix_rend, false);
			column_pix_name.add_attribute (pix_rend, "pixbuf", 1);
			var name_rend = new CellRendererText ();
			name_rend.set_property ("ellipsize", Pango.EllipsizeMode.END);
			column_pix_name.pack_start (name_rend, true);
			column_pix_name.add_attribute (name_rend, "text", 0);
			column_pix_name.set_resizable (true);
			column_pix_name.set_min_width (200);
			column_pix_name.set_max_width (400);
			column_pix_name.set_sort_column_id (0);

			var column_used_name = new TreeViewColumn ();
			column_used_name.set_title (_("Last Used"));
			this.treeview.append_column (column_used_name);
			var used_rend = new CellRendererText ();
			used_rend.set_property ("ellipsize", Pango.EllipsizeMode.END);
			column_used_name.pack_start (used_rend, true);
			column_used_name.add_attribute (used_rend, "text", 3);
			column_used_name.set_resizable (true);
			column_used_name.set_min_width (200);
			column_used_name.set_max_width (400);
			column_used_name.set_sort_column_id (4);
			used_rend.set_property("xalign", 0);
			
			var column_usage_name = new TreeViewColumn ();
			column_usage_name.set_title (_("Activity"));
			this.treeview.append_column (column_usage_name);
			var usage_rend = new UsageCellRenderer ();
			column_usage_name.pack_start (usage_rend, true);
			column_usage_name.add_attribute (usage_rend, "usage", 5);
			//column_usage_name.set_fixed_width (120);
			column_usage_name.set_sort_column_id (5);
			
			//FIXME Dirty hack for ordering automagically the treeview
			// without user input. We should call it twice because
			// the treeview is ordered ascending first.
			// Btw it's quick and simple...other ways for achieving this? -cando-
			column_usage_name.clicked ();column_usage_name.clicked ();
			
			var scroll = new ScrolledWindow (null, null);
			scroll.add (this.treeview);
			scroll.set_policy (PolicyType.NEVER, PolicyType.AUTOMATIC);
			scroll.set_shadow_type (ShadowType.IN);
			scroll.set_border_width (1);
			this.pack_start (scroll);
		}
	}
	
	public class ApplicationsChooserDialog : Gtk.Dialog {
		
		private ApplicationBlacklist app_blacklist;
		private AppSelectionTreeView treeview;

		GLib.HashTable<string, int64?> all_actors_list;
		GLib.HashTable<string, TreeIter?> actors_iter;

		private HashTable<string, AppChooseInfo> blocked_apps;
		private HashTable<string, AppChooseInfo> unblocked_apps;
		
		public ApplicationsChooserDialog (ApplicationBlacklist app_blacklist, 
				HashTable<string, AppChooseInfo> blocked_list, 
					HashTable<string, AppChooseInfo> unblocked_list) {
			this.app_blacklist = app_blacklist;

			this.blocked_apps = blocked_list;
			this.unblocked_apps = unblocked_list;
			this.actors_iter = new GLib.HashTable<string, TreeIter?>(str_hash, str_equal);
			this.set_title (_("Select Application"));
			this.set_destroy_with_parent (true);
			this.set_size_request (600, 400);
			this.set_skip_taskbar_hint (true);
			this.set_border_width (12);
			this.resizable = false;
			this.set_up_ui ();
			this.app_blacklist.get_all_applications(this);
			//this.populate_apps();
		}

		public TreeView tree {
			get {
				return treeview.tree;
			}
		}

		public ListStore liststore {
			get {
				return treeview.liststore;
			}
		}
		
		private int compare_dates(DateTime now, DateTime time) {
			int res = -1;
			int now_y, now_m, now_d, time_y, time_m, time_d;
			now.get_ymd(out now_y, out now_m, out now_d); 
			time.get_ymd(out time_y, out time_m, out time_d);
			if (now_y == time_y && now_m == time_m && now_d == time_d)
				return 0;
			else if (now_y == time_y && now_m == time_m && now_d == time_d + 1)
				return 1;
			return res;
		}
		
		public void handle_app_population(HashTable<string, int64?> all_actors) {
			all_actors_list = all_actors;

			GLib.List<AppInfo> all_infos = AppInfo.get_all();
			//uint size_actors = all_actors.size ();
			//float current_state = 10;
			//float step_dec = current_state/size_actors;

			GLib.List<AppInfo> other_appinfo = new GLib.List<AppInfo>();
			foreach(AppInfo app_info in all_infos)
			{
				string id = app_info.get_id ();
				int64? last_accessed_time = all_actors.lookup(id);
				if(last_accessed_time != null)
				{
					var time = new DateTime.from_unix_local (last_accessed_time/1000);
					var now = new DateTime.now_local();
					var res = this.compare_dates(now, time);
					string last_accessed = "";
					if (res == 0) // Today
						last_accessed = time.format(_("Today, %H:%M"));
					else if (res == 1) // Yesterday
						last_accessed = time.format(_("Yesterday, %H:%M"));
					else 
						last_accessed = time.format(_("%e %B %Y, %H:%M"));

					insert_liststore(app_info, last_accessed, last_accessed_time,
									0);
				}
				else {
					other_appinfo.append(app_info);
					insert_liststore(app_info, _("Never"), 0, 0);
				}
			}
			/*foreach(AppInfo app_info in other_appinfo)
			{
				insert_liststore(app_info, "", 0);
			}*/
		}

		public void insert_liststore(AppInfo app_info, string last_accessed, 
									int64 last_accessed_time, uint usage) {
			string id = app_info.get_id ();
			var name = app_info.get_name ();

			var icon = app_info.get_icon ();
			Gdk.Pixbuf? pix = ApplicationsTreeView.get_pixbuf_from_gio_icon (icon);

			AppChooseInfo app_choose_info = blocked_apps.lookup(id);
			if(app_choose_info == null)
			{
				TreeIter iter;
				this.treeview.liststore.append(out iter);
				this.treeview.liststore.set(iter, 0, name, 1, pix, 2, id,
											3, last_accessed, 4, last_accessed_time, 5, 0, -1);
				this.blocked_apps.insert(id, new AppChooseInfo(id, name, pix, 
																last_accessed, 
																last_accessed_time,
																usage));
				//this.actors_iter[id] = iter;
				if (last_accessed_time > 0)
					this.app_blacklist.get_count_for_app(id, iter, this.treeview.liststore); 
			}
			else
			{
				app_choose_info.last_accessed = last_accessed;
				app_choose_info.usage = 0;
			}
		}

		public void insert_app_liststore(string app) {
			AppChooseInfo app_choose_info = unblocked_apps.lookup(app);
			if(app_choose_info != null)
			{
				TreeIter iter;
				this.treeview.liststore.insert(out iter, 1);
				this.treeview.liststore.set(iter, 0, app_choose_info.name, 
					1, app_choose_info.icon, 2, app, 3, app_choose_info.last_accessed,
					4, app_choose_info.last_accessed_time, -1);
				this.app_blacklist.get_count_for_app(app_choose_info.get_id(), iter, this.treeview.liststore);
			}
		}

		private void set_up_ui () {
			this.treeview = new AppSelectionTreeView (this.app_blacklist);
			var area = this.get_content_area () as Gtk.Box;
			area.pack_start(this.treeview);
			this.add_buttons (Stock.CANCEL, ResponseType.CANCEL, Stock.OK, ResponseType.OK);
			
			this.treeview.show_all ();
		}
	}
	
	public class UsageCellRenderer : CellRenderer {

	private const int RECT_NUM = 10;
	private const int RECT_WIDTH = 5;
	private const int RECT_HEIGHT = 20;
	private const int RECT_SPACING = 3;
	private const int xpadding = 25;
	private const int ypadding = 10;
	
	private int usage_num;
	
	public int usage {
			get {
				return usage_num;
			}
			set {
				if(value > 10) usage_num = 10;
				else usage_num = value;
			}
		}
	
    public UsageCellRenderer () {
        GLib.Object ();
        this.usage_num = 0;
    }

    public override void get_size (Widget widget, Gdk.Rectangle? cell_area,
                                   out int x_offset, out int y_offset,
                                   out int width, out int height)
    {
        x_offset = xpadding;
        y_offset = ypadding;
        width = RECT_WIDTH * RECT_NUM + xpadding * 2 + RECT_SPACING * 9;
        height = RECT_HEIGHT + ypadding * 2;
    }

    /* render method */
    public override void render (Cairo.Context ctx, Widget widget,
                                 Gdk.Rectangle background_area,
                                 Gdk.Rectangle cell_area,
                                 CellRendererState flags)
    {
    	int x = cell_area.x + xpadding;
		int y = cell_area.y + ypadding;
		for (int i = 0; i < usage; i++)
		{
			ctx.set_source_rgb(0.4, 0.4, 0.4);
			ctx.rectangle(x, y, RECT_WIDTH, RECT_HEIGHT);
			ctx.fill();
			x += RECT_SPACING + RECT_WIDTH;
		}
		
		for (int i = 0; i < RECT_NUM - usage; i++)
		{
			ctx.set_source_rgb(0.7, 0.7, 0.7);
			ctx.rectangle(x, y, RECT_WIDTH, RECT_HEIGHT);
			ctx.fill();
			x += RECT_SPACING + RECT_WIDTH;
		}

	}
}
	
	public class AppChooseInfo {
		private string app_id;
		private string app_name;
		private Gdk.Pixbuf? app_icon;
		private string last_accessed_time_s;
		private int64 last_accessed_time_i;
		private uint usage_rating;

		public AppChooseInfo(string id, string app_name, Gdk.Pixbuf? app_icon, 
					string last_accessed_time_s, int64 last_accessed_time_i, uint usage_rating ) {
			this.app_name = app_name;
			this.app_icon = app_icon;
			this.last_accessed_time_s = last_accessed_time_s;
			this.last_accessed_time_i = last_accessed_time_i;
			this.usage_rating = usage_rating;
			this.app_id = id;
		}
		
		public string get_id () {
			return this.app_id;
		}
		
		public string name {
			get {
				return app_name;
			}
			set {
				app_name = value;
			}
		}

		public Gdk.Pixbuf? icon {
			get {
				return app_icon;
			}
			set {
				app_icon = value;
			}
		}

		public string last_accessed {
			get {
				return last_accessed_time_s;
			}
			set {
				last_accessed_time_s = value;
			}
		}
		
		public int64 last_accessed_time {
			get {
				return last_accessed_time_i;
			}
			set {
				last_accessed_time_i = value;
			}
		}

		public uint usage {
			get {
				return usage_rating;
			}
			set {
				usage_rating = value;
			}
		}
	}
}

