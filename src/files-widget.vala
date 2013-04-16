/* -*- Mode: vala; tab-width: 4; intend-tabs-mode: t -*- */
/* alm
 *
 * Copyright (C) 2012 Seif Lotfy <seif@lotfy.com>
 * Copyright (C) 2012 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright (C) 2012 Intel Corp.
 *               Authored by: Seif Lotfy <seif.lotfy@collabora.co.uk>
 * Copyright (C) 2012 Stefano Candori <stefano.candori@gmail.com>
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
using Zeitgeist;

namespace Alm {

	public class FileTypeBlacklist {
		private Blacklist blacklist_interface;
		private HashMap<string, CheckButton> checkboxes;

		public static string interpretation_prefix = "interpretation-";
		
		public FileTypeBlacklist (Blacklist blacklist_inter,
					HashMap<string, CheckButton> all_checkboxes) {
			blacklist_interface = blacklist_inter;
			checkboxes = all_checkboxes;
		}

		private string get_name(string interpretation) {
			var names = interpretation.split("#");
			var name = names[names.length-1].down();
			return "%s%s".printf(interpretation_prefix, name);
		}

		public void populate_file_types() {

			foreach(string key in blacklist_interface.all_templates.get_keys()) {
				if(key.has_prefix(this.interpretation_prefix))
				{
					var inter = blacklist_interface.all_templates[key].get_subject(0).get_interpretation ();
					if(checkboxes.has_key(inter))
						checkboxes.get(inter).active = true;
				}
			}
		}

		public void block(string interpretation) {
			Event ev = new Event();
			Subject sub = new Subject();
			sub.set_interpretation(interpretation);
			ev.add_subject(sub);

			blacklist_interface.add_template(
					this.get_name(interpretation), ev);
		}

		public void unblock(string interpretation) {
			blacklist_interface.remove_template(
					this.get_name(interpretation));
		}
	}

	public class PathBlacklist {
		private Blacklist blacklist_interface;

		public static string folder_prefix = "dir-";
		private static string suffix = "/*";

		private HashSet<string> all_blocked_folder;

		public signal void folder_added(string path);

		public signal void folder_removed(string path);
		
		public PathBlacklist (Blacklist blacklist_inter) {
			blacklist_interface = blacklist_inter;
			this.blacklist_interface.template_added.connect(on_blacklist_added);
			this.blacklist_interface.template_removed.connect(on_blacklist_removed);

			this.get_blocked_folder ();
		}

		public HashSet<string> all_folders {
			get {
				return all_blocked_folder;
			}
		}

		public bool is_duplicate (string path) {
			return all_blocked_folder.contains (path);
		}

		private void get_blocked_folder () {
			all_blocked_folder = new HashSet<string>();

			foreach(string key in blacklist_interface.all_templates.get_keys()) {
				if(key.has_prefix(folder_prefix))
				{
					string folder = get_folder(blacklist_interface.all_templates.get(key));
					if(folder != null)
						all_blocked_folder.add(folder);
				}
			}
		}

		private void on_blacklist_added (string blacklist_id, Event ev) {
			if(blacklist_id.has_prefix(folder_prefix))
			{
				string uri = get_folder(ev);
				if(uri != null)
				{
					folder_added(uri);
					if(!all_blocked_folder.contains(uri))
						all_blocked_folder.add(uri);
				}
			}
		}

		private void on_blacklist_removed (string blacklist_id, Event ev) {
			if(blacklist_id.has_prefix(folder_prefix))
			{
				string uri = get_folder(ev);
				if(uri != null)
				{
					folder_removed(uri);
					if(all_blocked_folder.contains(uri))
						all_blocked_folder.remove(uri);
				}
			}
		}

		private string get_folder(Event ev) {
			Subject sub = ev.get_subject(0);
			string uri = sub.get_uri ();
			uri = uri.replace(suffix, "");
			File blocked_uri = File.new_for_uri(uri);
			
			string final_path = blocked_uri.query_exists(null)? blocked_uri.get_path(): null;

			return final_path;
		}

		public void block(string folder) {
			Event ev = new Event ();
			Subject sub = new Subject ();
			
			File block_path = File.new_for_path(folder);
			string uri = "%s%s".printf(block_path.get_uri(), suffix);
			sub.set_uri(uri);
			ev.add_subject(sub);

			blacklist_interface.add_template(
					"%s%s".printf(folder_prefix, folder), ev);

			if(!all_blocked_folder.contains(folder))
					all_blocked_folder.add(folder);
		}

		public void unblock(string folder) {
			blacklist_interface.remove_template(
					"%s%s".printf(folder_prefix, folder));

			if(all_blocked_folder.contains(folder))
					all_blocked_folder.remove(folder);
		}
	}


	public class FilesWidget : Gtk.Box {

		private FileTypeBlacklist files_type_blacklist;
		private PathBlacklist path_blacklist;
		private TreeView folder_list;
		private ListStore folder_list_store;

		private HashMap<string, string> mime_dict;
		private HashMap<string, CheckButton> checkboxes;
		private HashSet<CheckButton> button_list;

		private HashMap<string, UserDirectory> defined_dirs;

		private Blacklist blacklist;
		private bool file_type_fire_signal = true;

		private IconTheme icon_theme;
		private Gdk.Pixbuf? stock_folder_icon;

		enum TreeViewCols
		{
			APP_NAME,
			ICON,
			DESKTOP_FILE,
			N_COLS
		}

		public FilesWidget (Blacklist blacklist_interface) {
			Object (orientation: Orientation.VERTICAL);

			this.blacklist = blacklist_interface;
			this.checkboxes = new HashMap<string, CheckButton>();
			this.button_list = new HashSet<CheckButton>();
			this.icon_theme = new IconTheme();

			this.files_type_blacklist = new FileTypeBlacklist(blacklist_interface, 
												this.checkboxes);
			this.path_blacklist = new PathBlacklist(blacklist_interface);

			blacklist_interface.template_added.connect(
				(blacklist_id, blacklist_template) => {
					if(blacklist_id.has_prefix(FileTypeBlacklist.interpretation_prefix))
					{
						file_type_fire_signal = false;
						var inter = blacklist_template.get_subject(0).get_interpretation ();
						if(checkboxes.has_key(inter))
							checkboxes.get(inter).active = true;
						file_type_fire_signal = true;
					}
				});
			blacklist_interface.template_removed.connect(
				(blacklist_id, blacklist_template) => {
					if(blacklist_id.has_prefix(FileTypeBlacklist.interpretation_prefix))
					{
						file_type_fire_signal = false;
						var inter = blacklist_template.get_subject(0).get_interpretation ();
						if(checkboxes.has_key(inter))
							checkboxes.get(inter).active = false;
						file_type_fire_signal = true;
					}
				});

			this.path_blacklist.folder_added.connect((folder) => {
				if(!this.path_blacklist.is_duplicate(folder))
					add_folder_to_view(folder);
			});

			this.path_blacklist.folder_removed.connect((folder) => {
				remove_folder_from_view(folder);
			});

			mime_dict = new HashMap<string, string>(str_hash, str_equal);
			mime_dict.set(_("Audio"), NFO_AUDIO);
	        mime_dict.set(_("Video"), NFO_VIDEO);
	        mime_dict.set(_("Image"), NFO_IMAGE);
	        mime_dict.set(_("Text"), NFO_DOCUMENT);
	        mime_dict.set(_("Presentation"), NFO_PRESENTATION);
	        mime_dict.set(_("Spreadsheet"), NFO_SPREADSHEET);
	        mime_dict.set(_("Instant Messaging"), NMO_IMMESSAGE);
	        mime_dict.set(_("E-mail"), NMO_EMAIL);
	        mime_dict.set(_("Website"), NFO_WEBSITE);

			defined_dirs = new HashMap<string, UserDirectory>(str_hash, str_equal);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.DESKTOP), UserDirectory.DESKTOP);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.DOCUMENTS), UserDirectory.DOCUMENTS);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.DOWNLOAD), UserDirectory.DOWNLOAD);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.MUSIC), UserDirectory.MUSIC);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.PICTURES), UserDirectory.PICTURES);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.PUBLIC_SHARE), UserDirectory.PUBLIC_SHARE);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.TEMPLATES), UserDirectory.TEMPLATES);
			defined_dirs.set(Environment.get_user_special_dir(UserDirectory.VIDEOS), UserDirectory.VIDEOS);
		
			//FIXME: Not sure if the correct icon is being fetched for stock folder
			stock_folder_icon = this.render_icon_pixbuf(Stock.DIRECTORY, IconSize.LARGE_TOOLBAR);

			this.setup_ui();
		}

		private void setup_ui() {

			this.set_border_width(12);

			var vbox_file_types = new Box(Orientation.VERTICAL, 6);
			this.pack_start(vbox_file_types, false, false);

			// Label for Checkbox list
			var file_type_label = new Label(null);
			file_type_label.set_markup("<b>%s</b>".printf(_("Don't record activity for following type of files:")));
			file_type_label.set_alignment(0.0f, 0.5f);
			vbox_file_types.pack_start(file_type_label, false);

			// Checkbox Table
			var checkbox_table = new Table(3, 3, true);

			string[] keys = mime_dict.keys.to_array();
			for(int i=0,row=0,col=0; i < keys.length; i++, col++) {
			//foreach (var entry in mime_dict.entries) {
		        var check_button = new CheckButton.with_label (keys[i]);
				
				this.button_list.add(check_button);
				this.checkboxes.set(mime_dict[keys[i]], check_button);

				if(col > 2) {
					row++;
					col = col % 3;
				}

				checkbox_table.attach_defaults(check_button, col, col+1, row, row+1);
    		}
		
			vbox_file_types.pack_start(checkbox_table, false);

			this.files_type_blacklist.populate_file_types();

			foreach(CheckButton check_button in this.button_list)
			{
				check_button.toggled.connect(() => {
					if(file_type_fire_signal)
					{
						file_type_fire_signal = false;
						if(check_button.active)
							files_type_blacklist.block(mime_dict[check_button.label]);
						else
							files_type_blacklist.unblock(mime_dict[check_button.label]);
						file_type_fire_signal = true;
					}
    			});
			}

			// Horizontal Line
			var hoz_line = new HSeparator();
			this.pack_start(hoz_line, false, false, 12);

			// Folders
			var vbox_folders = new Box(Orientation.VERTICAL, 6);
			this.pack_start(vbox_folders, true, true);

			// Label for Folder list list
			var folders_label = new Label(null);
			folders_label.set_markup("<b>%s</b>".printf(_("Don't record activity in the following folders:")));
			folders_label.set_alignment(0.0f, 0.5f);
			vbox_folders.pack_start(folders_label, false);

			var file_chooser_vbox = new Box(Orientation.VERTICAL, 0);
			vbox_folders.pack_start(file_chooser_vbox, true, true);

			// Folder list TreeView
			this.folder_list_store = new ListStore (3, typeof(string), typeof(Gdk.Pixbuf?), typeof(string));
			this.folder_list = new TreeView.with_model (this.folder_list_store);
			this.folder_list.set_headers_visible (false);
			this.folder_list.set_rules_hint (true);

			var column_pix_name = new TreeViewColumn ();
			column_pix_name.set_title (_("Name"));
			this.folder_list.append_column (column_pix_name);
			
			var pix_rend = new FilesCellRenderer ();
			column_pix_name.pack_start (pix_rend, false);
			column_pix_name.add_attribute (pix_rend, "pixbuf", 1);
			column_pix_name.add_attribute (pix_rend, "text", 2);
			column_pix_name.add_attribute (pix_rend, "path", 0);
			
			var scroll = new ScrolledWindow(null, null);
			scroll.add(this.folder_list);
			scroll.set_policy (PolicyType.NEVER, PolicyType.AUTOMATIC);
			scroll.set_shadow_type (ShadowType.IN);
			scroll.set_border_width (1);
			file_chooser_vbox.pack_start(scroll, true, true);

			// Add Remove buttons
			var folder_toolbar = new Toolbar();
			folder_toolbar.toolbar_style = ToolbarStyle.ICONS;
			folder_toolbar.icon_size = 1;
			folder_toolbar.icon_size_set = true;
			folder_toolbar.visible = true;
			
			scroll.get_style_context().set_junction_sides(Gtk.JunctionSides.BOTTOM);
			folder_toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR);
		    folder_toolbar.get_style_context().set_junction_sides(Gtk.JunctionSides.TOP);

			var folder_add = new ToolButton(null, _("Add Folder"));
			folder_add.set_icon_name("list-add-symbolic");
			folder_add.clicked.connect(on_add_folder);

			var folder_remove = new ToolButton(null, _("Remove Folder"));
			folder_remove.set_icon_name("list-remove-symbolic");
			folder_remove.clicked.connect(on_remove_folder);

			folder_toolbar.insert(folder_add, 0);
			folder_toolbar.insert(folder_remove, 1);

			file_chooser_vbox.pack_start(folder_toolbar, false, false);
			this.folders_populate ();
		}

		private void folders_populate () {
			foreach(string folder in path_blacklist.all_folders)
			{
				add_folder_to_view(folder);
			}
		}

		private void on_add_folder() {
			var chooser = new FileChooserDialog(
				_("Select a directory to blacklist"), 
				null, FileChooserAction.SELECT_FOLDER);
			chooser.add_buttons (Stock.OK, ResponseType.OK, Stock.CANCEL, ResponseType.CANCEL);
			int res = chooser.run();
			chooser.hide();
			if(res == ResponseType.OK)
			{
				string folder = chooser.get_filename ();
				if(!this.path_blacklist.is_duplicate(folder))
				{
					add_folder_to_view(folder);
					this.path_blacklist.block(folder);
				}
			}
		}

		private void on_remove_folder () {
			TreeSelection sel = this.folder_list.get_selection ();
			if(sel != null)
			{
				TreeModel model;
				TreeIter iter;
				if(sel.get_selected(out model, out iter))
				{
					string folder;
					model.get(iter, 0, out folder);
					if(folder != null)
					{
						folder_list_store.remove(iter);
						this.path_blacklist.unblock(folder);
					}
				}
			}
		}

		private void add_folder_to_view (string folder) {

			Gdk.Pixbuf? icon = stock_folder_icon;
			ThemedIcon? nautilus_icon = null;
			if(defined_dirs.has_key(folder))
			{
				UserDirectory dir = defined_dirs.get(folder);
				if (dir.to_string() == "G_USER_DIRECTORY_DOCUMENTS")
					nautilus_icon = new ThemedIcon("folder-documents");
				else if (dir.to_string() == "G_USER_DIRECTORY_DOWNLOAD")
					nautilus_icon = new ThemedIcon("folder-download");
				else if (dir.to_string() == "G_USER_DIRECTORY_MUSIC")
					nautilus_icon = new ThemedIcon("folder-music");
				else if (dir.to_string() == "G_USER_DIRECTORY_DESKTOP")
					nautilus_icon = new ThemedIcon("user-desktop");
				else if (dir.to_string() == "G_USER_DIRECTORY_PICTURES")
					nautilus_icon = new ThemedIcon("folder-pictures");
				else if (dir.to_string() == "G_USER_DIRECTORY_VIDEOS")
					nautilus_icon = new ThemedIcon("folder-videos");
				else if (dir.to_string() == "G_USER_DIRECTORY_TEMPLATES")
					nautilus_icon = new ThemedIcon("folder-templates");
				else if (dir.to_string() == "G_USER_DIRECTORY_PUBLIC_SHARE")
					nautilus_icon = new ThemedIcon("folder-publicshare");
				if(nautilus_icon != null) {
					var pixbuf = ApplicationsTreeView.get_pixbuf_from_gio_icon(nautilus_icon, 24);
					if (pixbuf != null)
						icon = pixbuf;
				}
			}
			
			string name = Path.get_basename(folder.strip());
			TreeIter iter;
			this.folder_list_store.append(out iter);
			// First element is full path, second is icon and third is just the path basename
			this.folder_list_store.set(iter, 0, folder, 1, icon, 2, name, -1);
		}

		private bool remove_folder_from_view (string folder) {
			var model = this.folder_list.get_model ();
			TreeIter iter;
			model.get_iter_first (out iter);
			while (true)
			{
				Value can_app_value;
				model.get_value(iter, 0, out can_app_value);
				string cand_folder = can_app_value.get_string();
				if(folder == cand_folder)
				{
					this.folder_list_store.remove(iter);
					return true;
				}
				bool more_entires = model.iter_next(ref iter);
				if(!more_entires)
				{
					return false;
				}
			}
		}
	}

//Based on gnome-contacts contacts-cell-renderer-shape.vala
public class FilesCellRenderer : CellRenderer {

	private const int PIXBUF_SIZE = 24;
	private const int xspacing = 3; 
	
	private const int default_width = 60;
	private const int renderer_height = 50;
	
	private Widget current_widget;
	
	private Gdk.Pixbuf pixbuf_;
	private string text_;
	private string path_;
	
	public Gdk.Pixbuf pixbuf {
			get {
				return pixbuf_;
			}
			set {
				pixbuf_ = value;
			}
	}
	
	public string text {
			get {
				return text_;
			}
			set {
				text_ = value;
			}
	}
	
	public string path {
			get {
				return path_;
			}
			set {
				path_ = value;
			}
	}
	
	public FilesCellRenderer () {
		GLib.Object ();
	}
	
	private Pango.Layout get_text_layout (Widget widget,
					Gdk.Rectangle? cell_area,
					CellRendererState flags,
					string text,
					bool bold,
					int size) {
		Pango.Layout layout;
		int xpad;
		var attr_list = new Pango.AttrList ();

		layout = widget.create_pango_layout (text);

		var attr = new Pango.AttrSize (size * Pango.SCALE);
		attr.absolute = 1;
		attr.start_index = 0;
		attr.end_index = attr.start_index + text.length;
		attr_list.insert ((owned) attr);

		if (bold) {
			var desc = new Pango.FontDescription();
			desc.set_weight (Pango.Weight.BOLD);
			var attr_f = new Pango.AttrFontDesc (desc);
			attr_list.insert ((owned) attr_f);
		}
		layout.set_attributes (attr_list);

		get_padding (out xpad, null);

		layout.set_ellipsize (Pango.EllipsizeMode.END);

		Pango.Rectangle rect;
		int width, text_width;

		layout.get_extents (null, out rect);
		text_width = rect.width;

		if (cell_area != null)
			width = (cell_area.width - xpad) * Pango.SCALE;
		else
			width = default_width * Pango.SCALE;

		width = int.min (width, text_width);
		layout.set_width (width);

		Pango.Alignment align;
		if (widget.get_direction () == TextDirection.RTL)
			align = Pango.Alignment.RIGHT;
		else
			align = Pango.Alignment.LEFT;
		layout.set_alignment (align);

		return layout;
	}

	public override void get_size (Widget        widget,
				 Gdk.Rectangle? cell_area,
				 out int       x_offset,
				 out int       y_offset,
				 out int       width,
				 out int       height) {
		x_offset = y_offset = width = height = 0;
		// Not used
	}

	private void do_get_size (Widget       widget,
				Gdk.Rectangle? cell_area,
				Pango.Layout? layout,
				out int       x_offset,
				out int       y_offset) {
		Pango.Rectangle rect;
		int xpad, ypad;

		get_padding (out xpad, out ypad);

		layout.get_pixel_extents (null, out rect);

		if (cell_area != null) {
			rect.width  = int.min (rect.width, cell_area.width - 2 * xpad + xspacing);

		if (widget.get_direction () == TextDirection.RTL)
			x_offset = cell_area.width - (rect.width + xpad);
		else
			x_offset = xpad;

		x_offset = int.max (x_offset, 0);
		} else {
			x_offset = 0;
		}

		y_offset = ypad;
	}


	public override void render (Cairo.Context   cr,
			       Widget          widget,
			       Gdk.Rectangle   background_area,
			       Gdk.Rectangle   cell_area,
			       CellRendererState flags) {
		StyleContext context;
		Pango.Layout text_layout, path_layout;
		int text_x_offset = 0;
		int path_x_offset = 0;
		int text_y_offset = 0;
		int path_y_offset = 0;
		int xpad;
		Pango.Rectangle text_rect, path_rect;

		current_widget = widget;

		context = widget.get_style_context ();
		var font_size = context.get_font (StateFlags.NORMAL).get_size () / Pango.SCALE;
		get_padding (out xpad, null);

		text_layout = get_text_layout (widget, cell_area, flags, text, true, font_size);
		do_get_size (widget, cell_area, text_layout, out text_x_offset, out text_y_offset);
		text_layout.get_pixel_extents (null, out text_rect);
		text_x_offset = text_x_offset - text_rect.x;

		path_layout = get_text_layout (widget, cell_area, flags, path, false, font_size - 1);
		do_get_size (widget, cell_area, path_layout, out path_x_offset, out path_y_offset);
		path_layout.get_pixel_extents (null, out path_rect);
		path_x_offset = path_x_offset - path_rect.x;

		cr.save ();

		Gdk.cairo_rectangle (cr, cell_area);
		cr.clip ();

		Gdk.cairo_set_source_pixbuf (cr, this.pixbuf, cell_area.x, cell_area.y);
		cr.paint ();

		context.render_layout (cr,
				cell_area.x + text_x_offset + this.pixbuf.width+ xspacing ,
				cell_area.y + text_y_offset + 2,
				text_layout);
		context.render_layout (cr,
				cell_area.x + path_x_offset,
				cell_area.y + path_y_offset + renderer_height - 11 - path_layout.get_baseline () / Pango.SCALE,
				path_layout);
		cr.restore ();
	}
	
	public override void get_preferred_width (Widget       widget,
					    out int      min_width,
					    out int      nat_width) {
		int xpad;

		get_padding (out xpad, null);

		nat_width = min_width = xpad + default_width;
	}

	public override void get_preferred_height_for_width (Widget       widget,
						       int          width,
						       out int      minimum_height,
						       out int      natural_height) {
		int ypad;

		get_padding (null, out ypad);
		minimum_height = renderer_height + ypad;
		natural_height = renderer_height + ypad;
	}

	public override void get_preferred_height (Widget       widget,
					     out int      minimum_size,
					     out int      natural_size) {
		int min_width;

		get_preferred_width (widget, out min_width, null);
		get_preferred_height_for_width (widget, min_width,
					out minimum_size, out natural_size);
	}
}

}
