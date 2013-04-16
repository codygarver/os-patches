# -*- Mode: Makefile; indent-tabs-mode: t; tab-width: 2 -*-
#
# This file is part of Déjà Dup.
# For copyright information, see AUTHORS.
#
# Déjà Dup is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Déjà Dup is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Déjà Dup.  If not, see <http://www.gnu.org/licenses/>.

nobase_dist_data_DATA = \
	icons/hicolor/32x32/apps/activity-log-manager.svg \
	icons/hicolor/48x48/apps/activity-log-manager.svg

desktopdir = $(datadir)/applications
desktop_in_files = activity-log-manager.desktop.in activity-log-manager-ccpanel.desktop.in

if HAVE_CCPANEL
desktop_in_files+ = activity-log-manager-ccpanel.desktop.in
endif

desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

EXTRA_DIST = activity-log-manager.desktop.in activity-log-manager-ccpanel.desktop.in
CLEANFILES = activity-log-manager.desktop activity-log-manager-ccpanel.desktop 

check: $(desktop_DATA)
	for desktop in $(desktop_DATA); do \
		desktop-file-validate $${desktop}; \
	done

gtk_update_icon_cache = gtk-update-icon-cache -f -t
install-data-hook: update-icon-cache
uninstall-hook: update-icon-cache

update-icon-cache:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating Gtk icon cache."; \
		$(gtk_update_icon_cache) $(datadir)/icons/hicolor; \
	else \
		echo "*** Icon cache not updated.  After (un)install, run these:"; \
		echo "***   $(gtk_update_icon_cache) $(datadir)/icons/hicolor"; \
	fi
