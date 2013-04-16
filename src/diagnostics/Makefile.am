if HAVE_CCPANEL
ccpaneldir = $(CCPANEL_DIR)
bin_PROGRAMS = whoopsie-preferences
endif

policykitdir = $(datadir)/polkit-1/actions/
dbussystemdir = $(sysconfdir)/dbus-1/system.d/
dbusservicedir = $(datadir)/dbus-1/system-services/
gnomeccuidir = $(datadir)/gnome-control-center/ui/

whoopsie_preferences_CFLAGS = \
	-Wall \
	-g \
	$(POLKIT_CFLAGS) $(GIO_UNIX_CFLAGS)

whoopsie_preferences_SOURCES = \
	whoopsie-generated.c whoopsie-generated.h whoopsie-preferences.c

whoopsie_preferences_LDADD = \
	$(POLKIT_LIBS) \
	$(GIO_UNIX_LIBS)

policykit_in_files = \ 
	com.ubuntu.whoopsiepreferences.policy.in

EXTRA_DIST = \
	whoopsie-preferences.xml \
	com.ubuntu.WhoopsiePreferences.service \
	com.ubuntu.WhoopsiePreferences.conf \
	$(policykit_in_files) \
	whoopsie.ui

gnomeccui_DATA = \
	whoopsie.ui
policykit_DATA = \
	$(policykit_in_files:.policy.in=.policy)
dbussystem_DATA = \
	com.ubuntu.WhoopsiePreferences.conf
dbusservice_DATA = \
	com.ubuntu.WhoopsiePreferences.service

whoopsie-generated.c: whoopsie-preferences.xml
	gdbus-codegen --interface-prefix com.ubuntu. \
		--generate-c-code whoopsie-generated \
		$<

CLEANFILES = whoopsie-generated.[ch] \
	$(policykit_DATA)
@INTLTOOL_POLICY_RULE@
