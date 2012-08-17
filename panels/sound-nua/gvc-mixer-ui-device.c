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

#include <string.h>
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


/**
 * get_profile_canonical_name - removes the part of the string that starts with
 * skip_prefix, i e corresponding to the other direction. Normally either
 * "input:" or "output:"
 * @returns string must be freed by user 
 */
static gchar *
get_profile_canonical_name(const gchar *profile_name, const gchar *skip_prefix)
{
    gchar *result = g_strdup(profile_name);
    gchar *c = result;
   
    while (*c) {
        /* Find '\0' or past next '+' */
        gchar *d = c;
        while (*d) {
            if (*d == '+') {
               d++;
               break;
            }
            d++;
        }

        if (g_str_has_prefix(c, skip_prefix)) {
            /* It's the other direction, so remove it from result */
            gchar *newresult;
            int i = c - result;
            result[i] = '\0';
            newresult = g_strjoin("", result, d, NULL);
            g_free(result);
            result = newresult;
            c = result + i; 
        }
        else 
            c = d;
    }
    
    /* Cut a final '+' off */
    if (g_str_has_suffix(result, "+"))
        result[strlen(result)-1] = '\0';

    return result;
}

const gchar*
gvc_mixer_ui_device_get_matching_profile (GvcMixerUIDevice *device, const gchar *profile)
{
	gchar *skip_prefix = device->priv->type == UiDeviceInput ? "output:" : "input:";
	gchar *target_cname = get_profile_canonical_name(profile, skip_prefix);
	GList *t, *values = g_hash_table_get_values(device->priv->profiles);
	gchar *result = NULL;

	for (t = values; t != NULL; t = t->next) {
		GvcMixerCardProfile* p = t->data;
		gchar *canonical_name = get_profile_canonical_name(p->profile, skip_prefix);
        g_debug("analysing %s", p->profile);
		if (!strcmp(canonical_name, target_cname)) {
			result = p->profile;
		}
		g_free(canonical_name);
    }

	g_free(target_cname);
	g_debug("Matching profile for '%s' is '%s'", profile, result ? result : "(null)");
	return result;
}


/** gvc_mixer_ui_device_set_profiles
   @param in_profiles a list of GvcMixerCardProfile
   assigns value to
    * device->priv->profiles (profiles to be added to combobox)
    * device->priv->supported_profiles (all profiles of this port)
    * device->priv->disable_profile_swapping (whether to show the combobox)
*/
void
gvc_mixer_ui_device_set_profiles (GvcMixerUIDevice *device, const GList *in_profiles)
{
	g_debug ("=== SET PROFILES === '%s'", gvc_mixer_ui_device_get_description(device));
		
	GList* t;
	GHashTable *profile_descriptions;
	GHashTable *added_profiles; 
	int only_canonical;
	gchar *skip_prefix = device->priv->type == UiDeviceInput ? "output:" : "input:";
	
	if (in_profiles == NULL)
		return;

	device->priv->supported_profiles = g_list_copy ((GList*) in_profiles);

	added_profiles = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
    
	/* Run two iterations: First, add profiles which are canonical themselves,
	   Second, add profiles for which the canonical name is not added already 
	*/
	for (only_canonical = 1; only_canonical >= 0; only_canonical--) {
    	for (t = (GList *) in_profiles; t != NULL; t = t->next) {
			GvcMixerCardProfile* p = t->data;
			gchar *canonical_name = get_profile_canonical_name(p->profile, skip_prefix);
			g_debug("The canonical name for '%s' is '%s'", p->profile, canonical_name);

			/* Have we already added the canonical version of this profile? */
			if (g_hash_table_contains(added_profiles, canonical_name)) {
				g_free(canonical_name);
				continue;
			}

			if (only_canonical && strcmp(p->profile, canonical_name)) {
				g_free(canonical_name);
				continue;
            }

			g_free(canonical_name);

			g_debug("Adding profile to combobox: '%s' - '%s'", p->profile, p->human_profile);
            g_hash_table_insert(added_profiles, g_strdup(p->profile), p);
            g_hash_table_insert(device->priv->profiles, g_strdup(p->human_profile), p);
        }
    }

    /* TODO: Consider adding the "Off" profile here */

	device->priv->disable_profile_swapping = g_hash_table_size(added_profiles) <= 1;
    
    g_hash_table_destroy(added_profiles);
}

/** gvc_mixer_ui_device_get_best_profile
  * @param selected the selected profile or its canonical name - can be NULL
  * if any profile is okay
  * @param current the currently selected profile
  * @returns a profile name, does not need to be freed, valid as long as the 
  * ui device profiles are
  */
const gchar* 			
gvc_mixer_ui_device_get_best_profile (GvcMixerUIDevice *device, const gchar *selected, 
const gchar *current)
{
	GList *t;
	GList *candidates = NULL;
	const gchar *result = NULL;
	gchar *skip_prefix = device->priv->type == UiDeviceInput ? "output:" : "input:";
    gchar *canonical_name_selected = NULL;

	/* First make a list of profiles acceptable to switch to */
	if (selected) 
		canonical_name_selected = get_profile_canonical_name(selected, skip_prefix);

	for (t = device->priv->supported_profiles; t != NULL; t = t->next) {
		GvcMixerCardProfile* p = t->data;
		gchar *canonical_name = get_profile_canonical_name(p->profile, skip_prefix);
		if (!canonical_name_selected || !strcmp(canonical_name, canonical_name_selected)) {
			candidates = g_list_append(candidates, p);
			g_debug("Candidate for profile switching: '%s'", p->profile);
		}
	}

	if (!candidates) {
		g_warning("No suitable profile candidates for '%s'", selected ? selected : "(null)");
		g_free(canonical_name_selected);
		return current; 
	}

	/* 1) Maybe we can skip profile switching altogether? */
	for (t = candidates; (result == NULL) && (t != NULL); t = t->next) {
		GvcMixerCardProfile* p = t->data;		
		if (!strcmp(current, p->profile))
			result = p->profile;
	}

	/* 2) Try to keep the other side unchanged if possible */
	if (result == NULL) {
		guint prio = 0;
		gchar *skip_prefix_reverse = device->priv->type == UiDeviceInput ? "input:" : "output:";
		gchar *current_reverse = get_profile_canonical_name(current, skip_prefix_reverse);
		for (t = candidates; t != NULL; t = t->next) {
			GvcMixerCardProfile* p = t->data;
			gchar *p_reverse = get_profile_canonical_name(p->profile, skip_prefix_reverse);
			g_debug("Comparing '%s' (from '%s') with '%s', prio %d", p_reverse, p->profile, current_reverse, p->priority); 
			if (!strcmp(p_reverse, current_reverse) && (!result || p->priority > prio)) {
				result = p->profile;
				prio = p->priority;
			}
			g_free(p_reverse);
		}
		g_free(current_reverse);
	}

	/* 3) All right, let's just pick the profile with highest priority. 
		TODO: We could consider asking a GUI question if this stops streams 
		in the other direction */
	if (result == NULL) {
		guint prio = 0;
		for (t = candidates; t != NULL; t = t->next) {
			GvcMixerCardProfile* p = t->data;
			if ((p->priority > prio) || !result) {
				result = p->profile;
				prio = p->priority;
			}
		}
	}

	g_list_free(candidates);
	g_free(canonical_name_selected);
	return result;
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

