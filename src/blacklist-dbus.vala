/* -*- Mode: vala; tab-width: 4; intend-tabs-mode: t -*- */
/* alm
 *
 * Copyright (C) 2012 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright (C) 2011 Collabora Ltd.
 *             Authored by Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             Authored by Seif Lotfy <seif@lotfy.com>
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

using Zeitgeist;
using Gtk;

namespace Alm {

	[DBus (name = "org.gnome.zeitgeist.Blacklist")]
	interface BlacklistInterface : Object {

	    public abstract void add_template (string blacklist_id, 
			[DBus (signature = "(asaasay)")] Variant blacklist_template) 
			throws IOError;

		[DBus (signature = "a{s(asaasay)}")]
	    public abstract Variant get_templates () throws IOError;


	    public abstract void remove_template(string blacklist_id) throws IOError;

	    public signal void template_added(string blacklist_id, 
			[DBus (signature = "s(asaasay)")] Variant blacklist_template);
	    public signal void template_removed(string blacklist_id, 
			[DBus (signature = "s(asaasay)")] Variant blacklist_template);
	}

	public delegate void ProcessFetchedEventsHandler (List<Event> evs);

	public class Blacklist {

		private BlacklistInterface blacklist;
		private HashTable<string, Event> blacklists;
		private Zeitgeist.Log log;

		// Incognito
		private string incognito_id = "block-all";
		private Event incognito_event;

		public Blacklist () {

			blacklist = Bus.get_proxy_sync (BusType.SESSION, "org.gnome.zeitgeist.Engine", 
											"/org/gnome/zeitgeist/blacklist");

			blacklist.template_added.connect(on_template_added);
			blacklist.template_removed.connect(on_template_removed);
			log = new Zeitgeist.Log();
			incognito_event = new Event();
		}

		public HashTable<string, Event> all_templates {
        	get {
				if(blacklists == null)
					this.get_templates();
				return blacklists;
			}
		}

		public signal void template_added(string blacklist_id, Event blacklist_template);

	    public signal void template_removed(string blacklist_id, Event blacklist_template);

	    public signal void incognito_toggled(bool status);

		public void add_template (string blacklist_id, Event blacklist_template) {
			blacklist.add_template(blacklist_id, blacklist_template.to_variant());
		}
		
		public void remove_template(string blacklist_id) {
			blacklist.remove_template(blacklist_id);
		}
		
		public void set_incognito(bool status) {
			// If status is true, means we want incognito to be set
			if(status)
				this.add_template(incognito_id, incognito_event);
			else
				this.remove_template(incognito_id);
		}

	    public HashTable<string, Event> get_templates() {
			Variant var_blacklists = blacklist.get_templates();
			blacklists = Utilities.from_variant(var_blacklists);

			return blacklists;
		}

		private void on_template_added(string blacklist_id, Variant blacklist_template) {
			Event ev = new Event.from_variant(blacklist_template);
			template_added(blacklist_id, ev);

			if(blacklist_id == incognito_id)
				incognito_toggled(true);

			blacklists.insert(blacklist_id, ev);
		}

	    private void on_template_removed(string blacklist_id, Variant blacklist_template) {
			Event ev = new Event.from_variant(blacklist_template);
			template_removed(blacklist_id, ev);

			if(blacklist_id == incognito_id)
				incognito_toggled(false);

			if(blacklists.lookup(blacklist_id) != null)
				blacklists.remove(blacklist_id);
		}

		public bool get_incognito() {
			if(blacklists == null)
				this.get_templates();

			foreach (Event ev in all_templates.get_values()) {
				if(Utilities.matches_event_template(ev, incognito_event))
					return true;
			}

			return false;
		}

		public async void find_events (string id, TreeIter iter, ListStore store)
		{
	     	Event event = new Event();
	    	event.set_manifestation (Zeitgeist.ZG_USER_ACTIVITY);
	    	event.set_actor ("application://"+id);
	    	
	    	PtrArray events = new PtrArray();
	    	events.add ((event as Object).ref());
	    	
	    	Event event2 = new Event();
	    	event2.set_manifestation (Zeitgeist.ZG_USER_ACTIVITY);
	    	Subject subj = new Subject ();
	    	subj.set_uri ("application://"+id);
	    	event2.add_subject(subj);
	    	
	    	events.add ((event2 as Object).ref());
	    	
	    	Array<int> results = yield log.find_event_ids (new TimeRange.anytime(),
	    	                                    (owned)events,
	    	                                    StorageState.ANY,
	    	                                    0,
	    	                                    ResultType.MOST_RECENT_EVENTS,
	    	                                    null);
	    	                                    
	    	var counter = results.length/100;
			store.set_value(iter, 5, counter);
		}

		public void get_count_for_app (string app_id, TreeIter iter, ListStore store) {
			find_events(app_id, iter, store);
		}
		
		public async void find_all_apps (ApplicationsChooserDialog dialog)
		{
	     	Event event = new Event();
	    	event.set_manifestation (Zeitgeist.ZG_USER_ACTIVITY);
	    	event.set_actor ("application://*");
	    	
	    	PtrArray events = new PtrArray();
	    	events.add ((event as Object).ref());
	    	
	    	Event event2 = new Event();
	    	event2.set_manifestation (Zeitgeist.ZG_USER_ACTIVITY);
	    	Subject subj = new Subject ();
	    	subj.set_uri ("application://*");
	    	event2.add_subject(subj);
	    	
	    	events.add ((event2 as Object).ref());
	    	
	    	events = new PtrArray();
	    	
	    	var results = yield log.find_events (new TimeRange.anytime(),
	    	                                    (owned)events,
	    	                                    StorageState.ANY,
	    	                                    0,
	    	                                    ResultType.MOST_POPULAR_ACTOR,
	    	                                    null);
	    	                                    
	    	HashTable<string, int64?> all_actors = new HashTable<string, int64?>(str_hash, str_equal);
			for(int i=0; i< results.size (); i++)
			{
				Event ev = results.next();
				if(ev != null);
				{
					string actor = ev.get_actor ();
					if(actor != null && actor.has_prefix("application://"))
						all_actors.insert(actor.substring(14), ev.get_timestamp ());
				}
			}
			dialog.handle_app_population(all_actors);
		}

		public void get_all_applications(ApplicationsChooserDialog dialog) {
			find_all_apps.begin (dialog);
		}
	}

	public class Utilities {
		public static bool matches_event_template (Event event, Event template_event)
        {
            if (!check_field_match (event.get_interpretation (), template_event.get_interpretation (), "ev-int"))
                return false;
            //Check if manifestation is child of template_event or same
            if (!check_field_match (event.get_manifestation (), template_event.get_manifestation (), "ev-mani"))
                return false;
            //Check if actor is equal to template_event actor
            if (!check_field_match (event.get_actor (), template_event.get_actor (), "ev-actor"))
                return false;
            //Check if origin is equal to template_event origin
			// Disabled since there is no way to retrieve origin using libzeitgeist
			// Previus versions of ALM didn't use event's origin field
            /*if (!check_field_match (event.origin, template_event.origin))
                return false;*/

            if (event.num_subjects () == 0)
                return true;

            for (int i = 0; i < event.num_subjects (); i++)
                for (int j = 0; j < template_event.num_subjects (); j++)
                    if (matches_subject_template (event.get_subject(i), template_event.get_subject(j)))
                        return true;

            return false;
        }

		public static bool matches_subject_template (Subject subject, Subject template_subject) {
            if (!check_field_match (subject.get_uri (), template_subject.get_uri (), "sub-uri"))
                return false;

			// Disabled since libzeitgeist cannot fetch current_uri
			// current_uri is not needed as previous implemenations of ALM used uri instead of current_uri
            /*if (!check_field_match (subject.current_uri, template_subject.current_uri))
                return false;*/
			// Interpretation

            if (!check_field_match (subject.get_interpretation (), template_subject.get_interpretation (), "sub-int"))
                return false;
            if (!check_field_match (subject.get_manifestation (), template_subject.get_manifestation (), "sub-mani"))
                return false;
            if (!check_field_match (subject.get_origin (), template_subject.get_origin (), "sub-origin"))
                return false;
            if (!check_field_match (subject.get_mimetype (), template_subject.get_mimetype (), "sub-mime"))
                return false;

            return true;
        }

		private static bool check_field_match (string? property, 
				string? template_property, string property_name="")
		{
			//debug ("Property Name %s", property_name);
     	    var matches = false;
	        var parsed = template_property;
	        var is_negated = template_property != null? parse_negation (ref parsed): false;
	
	        if (parsed == "")
	        {
	            return true;
	        }
	        else if (parsed == property)
	        {
	            matches = true;
    	    }
	
	        //debug ("Checking matches for %s", parsed);
	        //debug ("Returning %s", ((is_negated) ? !matches : matches).to_string());
	        return (is_negated) ? !matches : matches;
	    }

		public static bool parse_negation (ref string val)
	    {
	        if (!val.has_prefix ("!"))
	            return false;
	        val = val.substring (1);
	        return true;
	    }
	
		private const string SIG_EVENT = "asaasay";
	
		private const string SIG_BLACKLIST = "a{s("+SIG_EVENT+")}";

		public static HashTable<string, Event> from_variant (
            Variant templates_variant)
	    {
    	    var blacklist = new HashTable<string, Event> (str_hash, str_equal);
	
	        warn_if_fail (
	            templates_variant.get_type_string () == SIG_BLACKLIST);
	        foreach (Variant template_variant in templates_variant)
	        {
	            VariantIter iter = template_variant.iterator ();
	            string template_id = iter.next_value ().get_string ();
	            // FIXME: throw exception upon error instead of aborting
	            var ev_variant = iter.next_value ();
	            if(ev_variant != null)
	            {
		            Event template = new Event.from_variant (ev_variant);
		            blacklist.insert (template_id, template);
	            }	
	        }
	
	        return blacklist;
	    }

		public static Variant to_variant (HashTable<string, Event> blacklist) {
	        var vb = new VariantBuilder (new VariantType (SIG_BLACKLIST));
	        {
	            var iter = HashTableIter<string, Event> (blacklist);
	            string template_id;
	            Event event_template;
	            while (iter.next (out template_id, out event_template))
	            {
	                vb.open (new VariantType ("{s("+SIG_EVENT+")}"));
	                vb.add ("s", template_id);
	                vb.add_value (event_template.to_variant ());
                	vb.close ();
	            }
	        }
	        return vb.end ();
	    }
	}	   
}
