AC_INIT([activity-log-manager], 
        [0.9.4], 
        [http://bugs.launchpad,net/activity-log-manager])

AC_CONFIG_HEADERS([config.h])

AM_INIT_AUTOMAKE([1.11])

AM_SILENT_RULES([yes])

AC_PROG_CC
AM_PROG_CC_C_O
LT_INIT

AC_DEFINE_UNQUOTED(LOCALE_DIR, "${PREFIX}/${DATADIRNAME}/locale",[Locale directory])
AC_DEFINE_UNQUOTED(THEME_DIR, "${PREFIX}/${DATADIRNAME}/icons",[Icon directory])
AC_DEFINE_UNQUOTED(PKG_DATA_DIR, "${PREFIX}/${DATADIRNAME}/${PACKAGE}",[Package data directory])


dnl Check for vala
AM_PROG_VALAC([0.10.0])

IT_PROG_INTLTOOL([0.35.0])

GETTEXT_PACKAGE=activity-log-manager
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], ["$GETTEXT_PACKAGE"],
                   [The domain to use with gettext])
AM_GLIB_GNU_GETTEXT

PROGRAMNAME_LOCALEDIR=[${datadir}/locale]
AC_SUBST(PROGRAMNAME_LOCALEDIR)

PKG_CHECK_MODULES(ZEITGEIST, zeitgeist-1.0, [HAVE_LIBZG=yes], [HAVE_LIBZG=no])
PKG_CHECK_MODULES(GTK, gtk+-3.0, [HAVE_GTK=yes], [HAVE_GTK=no])
PKG_CHECK_MODULES(GEE, gee-1.0, [HAVE_GEE=yes], [HAVE_GEE=no])
PKG_CHECK_MODULES(GIO_UNIX, gio-unix-2.0, [HAVE_GIO_UNIX=yes], [HAVE_GIO_UNIX=no])
PKG_CHECK_MODULES(POLKIT, polkit-gobject-1, [HAVE_POLKIT=yes], [HAVE_POLKIT=no])

AC_ARG_WITH([extensiondir],
  [AS_HELP_STRING([--with-extensiondir],
    [use pkg-config extensiondir instead of PREFIX for plugins @<:@default=yes@:>@])],
  [],
  [with_extensiondir=yes])

AC_ARG_WITH([whoopsie],
  [AS_HELP_STRING([--with-whoopsie],
    [build control-center plugin Ubuntu crash reporting page @<:@default=check@:>@])],
  [with_ccpanel=yes],
  [with_whoopsie=check])
AC_ARG_WITH([ccpanel],
  [AS_HELP_STRING([--with-ccpanel],
    [build control-center plugin @<:@default=check@:>@])],
  [],
  [with_ccpanel=check])
AS_IF([test "x$with_ccpanel" != xcheck],
  [PKG_CHECK_MODULES(CCPANEL, libgnome-control-center,
    [AC_SUBST(CCPANEL_CFLAGS)
     AC_SUBST(CCPANEL_LIBS)]
     dnl Get control center extensions directory
     AS_IF([test "x$with_extensiondir" != xno],
       [CCPANEL_DIR=`$PKG_CONFIG --variable=extensiondir libgnome-control-center`],
       [CCPANEL_DIR="${PREFIX}/lib/control-center-1/panels"])
     AC_SUBST(CCPANEL_DIR),
    [if test "x$with_whoopsie" != xcheck; then
        AC_MSG_FAILURE(
          [--with-whoopsie was given, but test for libgnome-control-center failed])
      fi
      if test "x$with_ccpanel" != xcheck; then
        AC_MSG_FAILURE(
          [--with-ccpanel was given, but test for libgnome-control-center failed])
      fi
    ]
  )]
)
AM_CONDITIONAL([HAVE_CCPANEL], [test -n "$CCPANEL_LIBS"])
AM_CONDITIONAL([HAVE_WHOOPSIE], [test "x$with_whoopsie" != xcheck])
AS_IF([test "x$with_whoopsie" != xcheck],
    AC_DEFINE([HAVE_WHOOPSIE], [1],
    [Build control-center plugin Ubuntu crash reporting page]), [])



AC_OUTPUT([
Makefile
data/Makefile
src/Makefile
src/diagnostics/Makefile
po/Makefile.in
])
