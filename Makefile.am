## Process this file with automake to produce Makefile.in
## Created by Anjuta

SUBDIRS = src po data

INTLTOOL_FILES = intltool-extract.in \
                 intltool-merge.in \
                 intltool-update.in

almdocdir = ${prefix}/doc/alm
almdoc_DATA = \
	README\
	COPYING\
	AUTHORS\
	ChangeLog\
	INSTALL\
	NEWS


EXTRA_DIST = $(almdoc_DATA) $(INTLTOOL_FILES)

DISTCLEANFILES = \
	config.h config.status config.log \
	config.guess config.sub configure \
	intltool-extract intltool-merge \
	intltool-update po/.intltool-merge-cache

MAINTAINERCLEANFILES = Makefile.in aclocal.m4 config-h.in \
                       stamp-h.in depcomp install-sh ltmain.sh \
                       missing $(AUX_DIST)


# Remove doc directory on uninstall
uninstall-local:
	-rm -r $(almdocdir)
