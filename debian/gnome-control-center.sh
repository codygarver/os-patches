#!/bin/sh

# Support legacy applications that still refer to gnome-control-center in Unity
if [ "$XDG_CURRENT_DESKTOP" = "Unity" ] && [ -x /usr/bin/unity-control-center ]; then
  exec /usr/bin/unity-control-center $@
elif [ "XDG_CURRENT_DESKTOP" = "Pantheon" ] && [ -x /usr/bin/switchboard ]; then
  exec /usr/bin/switchboard $@
else
  exec /usr/bin/gnome-control-center.real $@
fi
