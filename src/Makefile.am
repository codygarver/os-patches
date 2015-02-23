## Process this file with automake to produce Makefile.in

INCLUDES = \
	-DPACKAGE_DATA_DIR=\""$(datadir)"\" \
	-DPACKAGE_LOCALE_DIR=\""$(prefix)/$(DATADIRNAME)/locale"\" \
	-DPACKAGE_LIB_DIR=\""$(libdir)"\" \
	-DUIDIR=\""$(datadir)/update-notifier/ui/"\" \
	$(PACKAGE_CFLAGS) $(APP_INDICATOR_CFLAGS)

bin_PROGRAMS = update-notifier \
		distro-cd-updater \
                local-avahi-notification \
                system-crash-notification



update_notifier_SOURCES = update-notifier.c \
                           update-notifier.h \
			   clipboard.c \
			   rfc822.h\
			   rfc822.c\
			   hooks.h\
			   hooks.c\
			   crash.c\
			   crash.h\
			   update.c\
			   update.h\
			   uevent.c\
			   uevent.h\
			   trayappletui.h\
			   trayappletui.c

distro_cd_updater_SOURCES = cdroms.c\
		             cdroms.h

local_avahi_notification_SOURCES = avahi.c\
                                    avahi.h

system_crash_notification_SOURCES = system-crash.c\
			             system-crash.h

update_notifier_LDADD = $(PACKAGE_LIBS) $(INTLLIBS) $(APP_INDICATOR_LIBS)
update_notifier_LDFLAGS = -export-dynamic

distro_cd_updater_LDADD = $(PACKAGE_LIBS) $(INTLLIBS)

local_avahi_notification_LDADD = $(PACKAGE_LIBS) $(INTLLIBS)

system_crash_notification_LDADD = $(PACKAGE_LIBS) $(INTLLIBS)
