load(qttest_p4)
SOURCES += tst_qobject.cpp

# this is here for a reason, moc_oldnormalizedobject.cpp is not auto-generated, it was generated by
# moc from Qt 4.6, and should *not* be generated by the current moc
SOURCES += moc_oldnormalizeobject.cpp

QT = core \
    network \
    gui
contains(QT_CONFIG, qt3support):DEFINES += QT_HAS_QT3SUPPORT
wince*: { 
    addFiles.files = signalbug.exe
    addFiles.path = .
    DEPLOYMENT += addFiles
}
symbian: { 
    addFiles.files = signalbug.exe
    addFiles.path = \\sys\\bin
    DEPLOYMENT += addFiles
}
