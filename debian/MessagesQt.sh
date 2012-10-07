#! /usr/bin/env bash
### TODO: transform Qt's translation template for KDE's Qt template
EXTRACTRC=${EXTRACTRC:-extractrc}
origdir=`pwd`
echo $qtcopydir
echo $podir
if test -d "$qtcopydir" -a -d "$podir"; then
	: # Noop
elif test -n "$qtcopydir" -o -n "$podir"; then
	echo "ERROR: MessageQt.sh was given wrong directory names!"
	exit 1
elif test -d ../qt-copy; then
	qtcopydir=../qt-copy
	podir=`pwd`/templates/messages/qt
elif test -d ../../qt-copy; then
	qtcopydir=../../qt-copy
	podir=`pwd`/../templates/messages/qt
else
	echo "ERROR: could not find qt-copy !"
        exit 1
fi
cd $qtcopydir/src || exit 2
$EXTRACTRC `find gui -name "qp*.ui"` > rc.cpp
xgettext --from-code=UTF-8 -C --kde -ci18n -ki18n:1 rc.cpp -o $podir/kdeqt.pot
rm rc.cpp
find . -name "*.cpp" | fgrep -v moc_ > list
### TODO: check that all classes below exist
for file in \
        qfiledialog qcolordialog \
	qurloperator qftp qhttp qlocal qerrormessage \
        q3filedialog q3colordialog q3printdialog \
	q3urloperator q3ftp q3http q3local q3errormessage \
        ; do
	fgrep -v $file list > list.new && mv list.new list
done

# Note about Qt contexts/comments:
# For Gettext purposes, comment of tr() and translate() is considered msgctxt.
# If translate() doesn't have a comment, but does have a context, then context
# is used for msgctxt. For info on handling this, see comments to method
# KLocale::translateQt in kdelibs/kdecore/localization/klocale.cpp
xgettext --join -C --qt \
    -ktranslate:1c,2,2t -ktranslate:2,3c,3t -ktr:1,1t -ktr:1,2c,2t \
    -kQT_TR_NOOP:1,1t -kQT_TRANSLATE_NOOP:1c,2,2t \
    --msgid-bugs-address=qt-bugs@trolltech.com \
    --files-from=list -o $podir/kdeqt.pot
cd $origdir
