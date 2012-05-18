/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- */
/*
 * gvc-mixer-ui-device.c
 * Copyright (C) Conor Curran 2011 <conor.curran@canonical.com>
 * 
 * gvc-mixer-ui-device.c is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * gvc-mixer-ui-device.c is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */


#include "gvc-mixer-ui-device.h"
#include "gvc-mixer-card.h"

#define GVC_MIXER_UI_DEVICE_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), GVC_TYPE_MIXER_UI_DEVICE, GvcMixerUIDevicePrivate))

static guint32 output_serial = 1;

struct GvcMixerUIDevicePrivate
{
	gchar*	     		first_line_desc;
	gchar*	     		second_line_desc;
	gint	     		card_id; 
	gchar*	     		port_name;
	gint	     		stream_id;
	guint	     		id;
	gboolean     		port_available;
	GList*       		supported_profiles;
	UiDeviceDirection 	type;
	GHashTable* 		profiles;
	gboolean 		disable_profile_swapping;
	gchar* 			user_preferred_profile;
};

enum
{
	PROP_0,
	PROP_DESC_LINE_1,
	PROP_DESC_LINE_2,
	PROP_CARD_ID,
	PROP_PORT_NAME,	
	PROP_STREAM_ID,
	PROP_UI_DEVICE_TYPE,
	PROP_PORT_AVAILABLE,
};

static void     gvc_mixer_ui_device_class_init (GvcMixerUIDeviceClass *klass);
static void     gvc_mixer_ui_device_init       (GvcMixerUIDevice      *op);
static void     gvc_mixer_ui_device_finalize   (GObject             *object);

G_DEFINE_TYPE (GvcMixerUIDevice, gvc_mixer_ui_device, G_TYPE_OBJECT);

static guint32
get_next_output_serial (void)
{
        guint32 serial;

        serial = output_serial++;

        if ((gint32)output_serial < 0) {
                output_serial = 1;
        }
        return serial;
}

static void
gvc_mixer_ui_device_get_property  (GObject       *object,
				   guint         property_id,
				   GValue 	 *value,
				   GParamSpec    *pspec)
{
	  GvcMixerUIDevice *self = GVC_MIXER_UI_DEVICE (object);

	  switch (property_id)
		{
		case PROP_DESC_LINE_1:
			g_value_set_string (value, self->priv->first_line_desc);
			break;
		case PROP_DESC_LINE_2:
			g_value_set_string (value, self->priv->second_line_desc);
			break;
		case PROP_CARD_ID:
			g_value_set_int (value, self->priv->card_id);
  			break;
		case PROP_PORT_NAME:
			g_value_set_string (value, self->priv->port_name);
			break;
		case PROP_STREAM_ID:
			g_value_set_int (value, self->priv->stream_id);
  			break;
		case PROP_UI_DEVICE_TYPE:
			g_value_set_uint (value, (guint)self->priv->type);
			break;
		case PROP_PORT_AVAILABLE:
			g_value_set_boolean (value, self->priv->port_available);
			break;
		default:
			G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
			break;
		}
}

static void
gvc_mixer_ui_device_set_property  (GObject      *object,
				guint         property_id,
				const GValue *value,
				GParamSpec   *pspec)
{
	  GvcMixerUIDevice *self = GVC_MIXER_UI_DEVICE (object);

	  switch (property_id)
		{
		case PROP_DESC_LINE_1:
			g_free (self->priv->first_line_desc);
			self->priv->first_line_desc = g_value_dup_string (value);
			g_debug ("gvc-mixer-output-set-property - 1st line: %s\n",
				 self->priv->first_line_desc);
			break;
		case PROP_DESC_LINE_2:
			g_free (self->priv->second_line_desc);
			self->priv->second_line_desc = g_value_dup_string (value);
			g_debug ("gvc-mixer-output-set-property - 2nd line: %s\n",
				 self->priv->second_line_desc);
			break;	
		case PROP_CARD_ID:
			self->priv->card_id = g_value_get_int (value);
			g_debug ("gvc-mixer-output-set-property - card id: %i\n",
				 self->priv->card_id);
			break;	
		case PROP_PORT_NAME:
			g_free (self->priv->port_name);
			self->priv->port_name = g_value_dup_string (value);
			g_debug ("gvc-mixer-output-set-property - card port name: %s\n",
				 self->priv->port_name);
			break;	
		case PROP_STREAM_ID:
			self->priv->stream_id = g_value_get_int (value);
			g_debug ("gvc-mixer-output-set-property - sink id: %i\n",
				 self->priv->stream_id);
			break;	
		case PROP_UI_DEVICE_TYPE:
			self->priv->type = (UiDeviceDirection)g_value_get_uint (value);
			break;
		case PROP_PORT_AVAILABLE:
			self->priv->port_available = g_value_get_boolean (value);
			g_debug ("gvc-mixer-output-set-property - port available %i, value passed in %i \n",
				 self->priv->port_available, g_value_get_boolean (value));
			break;			
		default:
			G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
			break;
	    }
}

static GObject *
gvc_mixer_ui_device_constructor (GType                  type,
			         guint                  n_construct_properties,
		                 GObjectConstructParam *construct_params)
{
        GObject         *object;
        GvcMixerUIDevice  *self;

        object = G_OBJECT_CLASS (gvc_mixer_ui_device_parent_class)->constructor (type, n_construct_properties, construct_params);

        self = GVC_MIXER_UI_DEVICE (object);
        self->priv->id = get_next_output_serial ();
        self->priv->profiles = g_hash_table_new_full (g_str_hash,
         					      g_str_equal,
         					      g_free,
         					      NULL);
	self->priv->stream_id = GVC_MIXER_UI_DEVICE_INVALID;
	self->priv->card_id = GVC_MIXER_UI_DEVICE_INVALID;
	self->priv->port_name = NULL;
	self->priv->disable_profile_swapping = FALSE;
	self->priv->user_preferred_profile = NULL;
        return object;
}

static void
gvc_mixer_ui_device_init (GvcMixerUIDevice *object)
{
	object->priv  = GVC_MIXER_UI_DEVICE_GET_PRIVATE (object);	
}

static void 
gvc_mixer_ui_device_dispose (GObject *object)
{
        g_return_if_fail (object != NULL);
        g_return_if_fail (GVC_MIXER_UI_DEVICE (object));

	GvcMixerUIDevice *device;
	device = GVC_MIXER_UI_DEVICE (object);
	
	if (device->priv->port_name != NULL){
		g_free (device->priv->port_name);
		device->priv->port_name = NULL;
	}
	if (device->priv->first_line_desc != NULL){		
		g_free (device->priv->first_line_desc);
		device->priv->first_line_desc = NULL;
	}
	if (device->priv->second_line_desc != NULL){
		g_free (device->priv->second_line_desc);
		device->priv->second_line_desc = NULL;
	}
	if (device->priv->profiles != NULL){
		g_hash_table_destroy (device->priv->profiles);
		device->priv->profiles = NULL;
	}
	if (device->priv->user_preferred_profile != NULL){
		g_free (device->priv->user_preferred_profile);
		device->priv->user_preferred_profile = NULL;
	}
    G_OBJECT_CLASS (gvc_mixer_ui_device_parent_class)->dispose (object);	
}

static void
gvc_mixer_ui_device_finalize (GObject *object)
{
	G_OBJECT_CLASS (gvc_mixer_ui_device_parent_class)->finalize (object);
}

static void
gvc_mixer_ui_device_class_init (GvcMixerUIDeviceClass *klass)
{
	GObjectClass* object_class = G_OBJECT_CLASS (klass);

	object_class->constructor = gvc_mixer_ui_device_constructor;
	object_class->dispose = gvc_mixer_ui_device_dispose;        
	object_class->finalize = gvc_mixer_ui_device_finalize;
	object_class->set_property = gvc_mixer_ui_device_set_property;
	object_class->get_property = gvc_mixer_ui_device_get_property;

	GParamSpec *pspec;

	pspec = g_param_spec_string ("description",
				"Description construct prop",
				"Set first line description",
				"no-name-set",
				G_PARAM_READWRITE);
	g_object_class_install_property (object_class,
					 PROP_DESC_LINE_1,
					 pspec);	
				 
	pspec = g_param_spec_string ("origin",
				 "origin construct prop",
				 "Set second line description name",
				 "no-name-set",
				  G_PARAM_READWRITE);
	g_object_class_install_property (object_class,
					PROP_DESC_LINE_2,
					pspec);	

	pspec = g_param_spec_int ("card-id",
				  "Card id from pulse",
				  "Set/Get card id",
				  -1 ,
				  1000 ,
				  GVC_MIXER_UI_DEVICE_INVALID,
				  G_PARAM_READWRITE);

	g_object_class_install_property (object_class,
					 PROP_CARD_ID,
					 pspec);
				 				 
	pspec = g_param_spec_string ("port-name",
				 "port-name construct prop",
				 "Set port-name",
				 NULL,
				 G_PARAM_READWRITE);
	g_object_class_install_property (object_class,
					 PROP_PORT_NAME,
					 pspec);	

	pspec = g_param_spec_int ("stream-id",
				  "stream id assigned by gvc-stream",
				  "Set/Get stream id",
				  -1,  
				   10000, 
				   GVC_MIXER_UI_DEVICE_INVALID,
				   G_PARAM_READWRITE);
	g_object_class_install_property (object_class,
					 PROP_STREAM_ID,
					 pspec);

	pspec = g_param_spec_uint ("type",
				   "ui-device type",
				   "determine whether its an input and output",
     				0,
				    1,
				    0,
				    G_PARAM_READWRITE);
	g_object_class_install_property (object_class,
					 PROP_UI_DEVICE_TYPE,
					 pspec);

	pspec = g_param_spec_boolean ( "port-available",
					"available",
					"determine whether this port is available",
					FALSE,
					G_PARAM_READWRITE);				       
	g_object_class_install_property (object_class,
					PROP_PORT_AVAILABLE,
					pspec);        
				 
	g_type_class_add_private (klass, sizeof (GvcMixerUIDevicePrivate));					 				
}

/*
 gvc_mixer_ui_device_set_profiles (GvcMixerUIDevice *device, const GList *in_profiles)

 This method attempts to reduce the list of profiles visible to the user by figuring out 
 from the context of that device (whether it's an input or an output) what profiles actually provide an alternative.
 
 It does this by the following.
  - It ignores off profiles.
  - Sorts the incoming profiles by attempting to split each profile on the char '+'.
     -- This will pull out the relevant aspect of the profile for the type of device this is.
        e.g stereo analog out, bluetooth or HDMI for an output, stereo analog in or bluetooth for the input coming from  
        a typical setup of a onboard HDA intel card and bluetooth headset.
     -- Will store this shortened string against the profile full length name.
 
  - Next it tries to determine from our prepared hash above if we want to allow the user to change
    the profile on the device i.e.  if the profile combo should be visible to the user on the UI.
    -- Is there any actual choice or just much of the same thing from the 
       context of the direction on this device.
  -If there is a choice
    -- It will gather the groups of identical profiles and choose the one that has the highest priority to insert
       into the final list to be presented to the user.
    - if the shortened profiles are identical so that the profile combo is to be hidden from the user
     -- It will choose the profile with the highest priority. (the pattern assumes a device will always have a profile in it's profile list)
Note: 
 I think this algorithm is inherently flawed.
 https://bugs.launchpad.net/ubuntu/+source/gnome-control-center/+bug/972554
 An issue arises in this bug whereby the user needs to get at a specific profile which allows him a certain input and output
 configuration. But this algorithem because of priority values etc will reject that one profile that he needs to get at. 
TODO
 Optimise so as on the first pass you can 'choose' which profiles to hold on to and
 which are useles because they are essentially duplicates.
 => a depthfirst like approach is needed ...
*/
void
gvc_mixer_ui_device_set_profiles (GvcMixerUIDevice *device, const GList *in_profiles)
{
	g_debug ("\n SET PROFILES %s", gvc_mixer_ui_device_get_description(device));
		
	GList* t;
	GHashTable *profile_descriptions;
	
	if (in_profiles == NULL)
		return;
	
	device->priv->supported_profiles = g_list_copy (in_profiles);
	profile_descriptions = g_hash_table_new_full (g_str_hash,
	 					      g_str_equal,
	 					      g_free,
	 					      g_free);

	// Store each profile in a hash with the shortened relevant string as the key
	for (t = in_profiles; t != NULL; t = t->next) {

		GvcMixerCardProfile* p;
		p = t->data;
		
		if (g_strcmp0 (p->profile, "off") == 0) 
			continue;

		g_debug ("\n Attempt to split profile, p->profile %s on device %s \n",
	   			 p->profile,
	   			 gvc_mixer_ui_device_get_description (device));

		gchar** modified;

		modified = g_strsplit (p->profile, "+", 0);	
		guint count;
		
		count = g_strv_length (modified);
		// It's a profile that only handles one direction, cache it and move on
		if (count == 1){
			g_debug ("\n Single profile, key %s against value %s for device %s \n",
					 p->profile,
					 modified[0],
					 gvc_mixer_ui_device_get_description (device));
			g_hash_table_insert (profile_descriptions,
					 		     g_strdup (p->profile),
					 		     g_strdup (modified[0]));
			g_strfreev (modified);
			continue;
		}

		if (device->priv->type == UiDeviceOutput) {
			if (g_str_has_prefix (modified[0], "output")){
				g_debug ("\n Found an output profile - storing key %s against value %s for device %s \n",
						   p->profile,
						   modified[0],
						   gvc_mixer_ui_device_get_description (device));
				g_hash_table_insert (profile_descriptions,
						 		     g_strdup (p->profile),
						 		     g_strdup (modified[0]));
			}
		}
		else{
			if (g_str_has_prefix (modified[1], "input")){
				g_debug ("\n Found an input profile - storing key %s against value %s for device %s \n",
					  p->profile, modified[1], gvc_mixer_ui_device_get_description (device));
				g_hash_table_insert (profile_descriptions,
				 		     g_strdup (p->profile),
				 		     g_strdup (modified[1]));
			}
		}
		g_strfreev (modified);				
	}
	
	// Determine if we want allow the user to change the profile from the device
	// i.e. is there any actual choice or just much of the same thing from the 
	// context of the direction on this device.
	gboolean identical = TRUE;
	GList *shortened_profiles;
	shortened_profiles = g_hash_table_get_values (profile_descriptions);
	
	for (t = shortened_profiles; t != NULL; t = t->next) {
		gchar* prof;
		prof = t->data;
		if (g_list_next (t) != NULL){
			gchar* next_prof;
			GList* n;
			n = g_list_next (t);
			next_prof = n->data;
			identical = g_strcmp0 (prof, next_prof) == 0; 
			g_debug ("try to compare %s with %s", prof, next_prof);
		}
		if (!identical){
			break;
		}
	}
	g_list_free (shortened_profiles);

	g_debug ("\n device->priv->disable_profile_swapping = %i \n", 
		  identical);

	device->priv->disable_profile_swapping = identical;
	GList *x;
	GList *y;

	if (!identical) {
		for (y = in_profiles; y != NULL; y = y->next) {
			GList *profiles_with_identical_shortened_names = NULL;
			GvcMixerCardProfile* p;
			p = y->data;
	
			if (g_strcmp0 (p->profile, "off") == 0) 
				continue;

			gchar* short_name;
			short_name = g_hash_table_lookup (profile_descriptions, p->profile);

			g_debug ("\n Not identical - examine  %s -> %s \n\n", short_name, p->profile);
			
			// If we have already populated for this short name - trust?? our prioritisation below and move on
			if (g_hash_table_contains (device->priv->profiles, short_name) == TRUE){
				g_debug ("\n already populated for %s => ignore %s \n", short_name, p->profile);
				continue;
			}		

			profiles_with_identical_shortened_names = g_list_append (profiles_with_identical_shortened_names, p);
				
			for (x = in_profiles; x != NULL; x = x->next) {
				GvcMixerCardProfile* l;
				l = x->data;
				gchar* other_modified;
		
				if (g_strcmp0 (l->profile, "off") == 0) 
					continue;

				// no point in comparing it against itself.								
				if (g_strcmp0 (p->profile, l->profile) == 0)
					continue;

				other_modified = g_hash_table_lookup (profile_descriptions, l->profile);
				
				if (g_strcmp0 (other_modified, short_name) == 0){
					profiles_with_identical_shortened_names = g_list_append (profiles_with_identical_shortened_names,
					 							 l);	
				}
			}
			// Algorithm flaw				
			GList* ordered = NULL;
			ordered = g_list_sort (profiles_with_identical_shortened_names,
			 		       (GCompareFunc) sort_profiles);	

			GvcMixerCardProfile* priority_profile = g_list_last(ordered)->data;

			g_debug ("\n Sensitive combo - Populate the profile combo with profile %s against short name %s",
			 	  priority_profile->profile, short_name);

			g_hash_table_insert (device->priv->profiles,
			 		     g_strdup(short_name),
					     priority_profile);
			g_list_free (profiles_with_identical_shortened_names);		
		}
	}
	else{
		// Since the profile list was already sorted on card port creation
		// we just need to take the last one as this will have the highest priority
		GvcMixerCardProfile* p = NULL;
		p = g_list_last (in_profiles)->data;
		if (p != NULL && p->human_profile != NULL)
			g_hash_table_insert (device->priv->profiles, 
					     p->human_profile,
					     p);		
	}
	/* DEBUG */
	/*GList* final_keys;
	final_keys = g_hash_table_get_keys (device->priv->profiles);
	GList* o;
	g_debug ("\n\n Profile population \n FOR DEVICE %s", gvc_mixer_ui_device_get_description (device));
	for (o = final_keys; o != NULL; o = o->next){
		gchar* key;
		key = o->data;
		GvcMixerCardProfile* l;
		l = g_hash_table_lookup (device->priv->profiles, key);
		g_debug ("\n key %s against \n profile %s \n", 
			key,
			l->profile);
	}*/
	g_hash_table_destroy (profile_descriptions);
}

gboolean
gvc_mixer_ui_device_should_profiles_be_hidden (GvcMixerUIDevice *device)
{
	return device->priv->disable_profile_swapping;
}

GHashTable*
gvc_mixer_ui_device_get_profiles (GvcMixerUIDevice *device)
{
	return device->priv->profiles; 
}

GList*
gvc_mixer_ui_device_get_supported_profiles (GvcMixerUIDevice *device)
{
	return device->priv->supported_profiles;
}

guint
gvc_mixer_ui_device_get_id (GvcMixerUIDevice *op)
{
        g_return_val_if_fail (GVC_IS_MIXER_UI_DEVICE (op), 0);
        return op->priv->id;
}

gint
gvc_mixer_ui_device_get_stream_id (GvcMixerUIDevice *op)
{
	gint sink_id;
	g_object_get (G_OBJECT (op),
		      "stream-id", &sink_id, NULL);
        return sink_id;			
}

void					
gvc_mixer_ui_device_invalidate_stream (GvcMixerUIDevice *self)
{
	self->priv->stream_id = GVC_MIXER_UI_DEVICE_INVALID;
}


const gchar*
gvc_mixer_ui_device_get_description (GvcMixerUIDevice *op)
{
	return op->priv->first_line_desc;
}

const gchar*
gvc_mixer_ui_device_get_origin (GvcMixerUIDevice *op)
{
	return op->priv->second_line_desc;
}

const gchar*
gvc_mixer_ui_device_get_user_preferred_profile (GvcMixerUIDevice *dev)
{
	return dev->priv->user_preferred_profile;
}

const gchar*
gvc_mixer_ui_device_get_top_priority_profile (GvcMixerUIDevice *dev)
{
	GList *last;
	last = g_list_last (dev->priv->supported_profiles);
	GvcMixerCardProfile *profile;
	profile = last->data;                        
	return profile->profile;
}

void 
gvc_mixer_ui_device_set_user_preferred_profile (GvcMixerUIDevice *device, const gchar* profile)
{
	if (device->priv->user_preferred_profile != NULL){
		g_free (device->priv->user_preferred_profile);
		device->priv->user_preferred_profile = NULL;
	}
	device->priv->user_preferred_profile = g_strdup (profile);
}

const gchar*
gvc_mixer_ui_device_get_port (GvcMixerUIDevice *op)
{
	return op->priv->port_name;
}

gboolean
gvc_mixer_ui_device_is_software (GvcMixerUIDevice *dev)
{
	return dev->priv->port_name == NULL && dev->priv->card_id == GVC_MIXER_UI_DEVICE_INVALID;
}

gboolean
gvc_mixer_ui_device_is_bluetooth (GvcMixerUIDevice *dev)
{
	return dev->priv->port_name == NULL && dev->priv->card_id != GVC_MIXER_UI_DEVICE_INVALID;	
}

gboolean
gvc_mixer_ui_device_is_output (GvcMixerUIDevice *dev)
{
	return dev->priv->type == UiDeviceOutput;	
}

