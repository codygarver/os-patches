if HAVE_CCPANEL
ccpaneldir = $(CCPANEL_DIR)
ccpanel_LTLIBRARIES = libactivity-log-manager.la
endif
if HAVE_WHOOPSIE
gnomeccuidir = $(datadir)/gnome-control-center/ui/
endif

SUBDIRS = diagnostics

VALAFLAGS = \
	--pkg zeitgeist-1.0 \
	--pkg gtk+-3.0 \
	--pkg gee-1.0  \
	--target-glib=2.26 \
	--pkg gio-unix-2.0 \
	config.vapi

bin_PROGRAMS = activity-log-manager

SHARED_CFLAGS = \
	-Wall \
	-g \
	-DPACKAGE_LOCALE_DIR=\""$(prefix)/$(DATADIRNAME)/locale"\" \
	-DPACKAGE_SRC_DIR=\""$(srcdir)"\" \
	-DPACKAGE_DATA_DIR=\""$(datadir)"\" \
	-DPROGRAMNAME_LOCALEDIR=\"${PROGRAMNAME_LOCALEDIR}\" \
	-DGETTEXT_PACKAGE=\"$(GETTEXT_PACKAGE)\" \
	$(GTK_CFLAGS) $(ZEITGEIST_CFLAGS) $(GEE_CFLAGS) $(GIO_UNIX_CFLAGS)
activity_log_manager_CFLAGS = \
	$(SHARED_CFLAGS)
libactivity_log_manager_la_CFLAGS = \
	$(SHARED_CFLAGS) \
	$(CCPANEL_CFLAGS)

if HAVE_WHOOPSIE
libactivity_log_manager_la_CFLAGS += \
	$(POLKIT_CFLAGS) \
	-DGNOMECC_UI_DIR=\""$(gnomeccuidir)"\"
endif

SOURCES = \
	activity-log-manager.vala \
	history-widget.vala \
	files-widget.vala \
	applications-widget.vala \
	blacklist-dbus.vala
activity_log_manager_SOURCES = \
	$(SOURCES) alm.vala 
libactivity_log_manager_la_SOURCES = \
	$(SOURCES:.vala=.c) alm-cc.c

if HAVE_WHOOPSIE
libactivity_log_manager_la_SOURCES += \
	diagnostics-widget.c \
	diagnostics/whoopsie-generated.c
endif

activity_log_manager_LDFLAGS = \
	-Wl,--export-dynamic
libactivity_log_manager_la_LDFLAGS = -module -avoid-version

SHARED_LIBS = \
	$(GTK_LIBS) \
	$(ZEITGEIST_LIBS) \
	$(GEE_LIBS) \
	$(GIO_UNIX_LIBS) \
	-lm
activity_log_manager_LDADD = \
	$(SHARED_LIBS)
libactivity_log_manager_la_LIBADD = \
	$(SHARED_LIBS) \
	$(CCPANEL_LIBS)

if HAVE_WHOOPSIE
libactivity_log_manager_la_LIBADD += \
	$(POLKIT_LIBS)
endif

GENERATED_C_FILES = $(alm_SOURCES:.vala=.c)

GENERATED_O_FILES = $(alm_SOURCES:.vala=.o)

CLEANFILES = \
	$(GENERATED_C_FILES) \
	$(GENERATED_O_FILES)
