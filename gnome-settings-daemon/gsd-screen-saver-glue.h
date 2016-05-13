/*
 * Generated by gdbus-codegen 2.46.1. DO NOT EDIT.
 *
 * The license of this code is the same as for the source it was derived from.
 */

#ifndef __GSD_SCREEN_SAVER_GLUE_H__
#define __GSD_SCREEN_SAVER_GLUE_H__

#include <gio/gio.h>

G_BEGIN_DECLS


/* ------------------------------------------------------------------------ */
/* Declarations for org.gnome.ScreenSaver */

#define GSD_TYPE_SCREEN_SAVER (gsd_screen_saver_get_type ())
#define GSD_SCREEN_SAVER(o) (G_TYPE_CHECK_INSTANCE_CAST ((o), GSD_TYPE_SCREEN_SAVER, GsdScreenSaver))
#define GSD_IS_SCREEN_SAVER(o) (G_TYPE_CHECK_INSTANCE_TYPE ((o), GSD_TYPE_SCREEN_SAVER))
#define GSD_SCREEN_SAVER_GET_IFACE(o) (G_TYPE_INSTANCE_GET_INTERFACE ((o), GSD_TYPE_SCREEN_SAVER, GsdScreenSaverIface))

struct _GsdScreenSaver;
typedef struct _GsdScreenSaver GsdScreenSaver;
typedef struct _GsdScreenSaverIface GsdScreenSaverIface;

struct _GsdScreenSaverIface
{
  GTypeInterface parent_iface;


  gboolean (*handle_get_active) (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation);

  gboolean (*handle_get_active_time) (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation);

  gboolean (*handle_lock) (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation);

  gboolean (*handle_set_active) (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation,
    gboolean arg_value);

  void (*active_changed) (
    GsdScreenSaver *object,
    gboolean arg_new_value);

};

GType gsd_screen_saver_get_type (void) G_GNUC_CONST;

GDBusInterfaceInfo *gsd_screen_saver_interface_info (void);
guint gsd_screen_saver_override_properties (GObjectClass *klass, guint property_id_begin);


/* D-Bus method call completion functions: */
void gsd_screen_saver_complete_lock (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation);

void gsd_screen_saver_complete_get_active (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation,
    gboolean active);

void gsd_screen_saver_complete_set_active (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation);

void gsd_screen_saver_complete_get_active_time (
    GsdScreenSaver *object,
    GDBusMethodInvocation *invocation,
    guint value);



/* D-Bus signal emissions functions: */
void gsd_screen_saver_emit_active_changed (
    GsdScreenSaver *object,
    gboolean arg_new_value);



/* D-Bus method calls: */
void gsd_screen_saver_call_lock (
    GsdScreenSaver *proxy,
    GCancellable *cancellable,
    GAsyncReadyCallback callback,
    gpointer user_data);

gboolean gsd_screen_saver_call_lock_finish (
    GsdScreenSaver *proxy,
    GAsyncResult *res,
    GError **error);

gboolean gsd_screen_saver_call_lock_sync (
    GsdScreenSaver *proxy,
    GCancellable *cancellable,
    GError **error);

void gsd_screen_saver_call_get_active (
    GsdScreenSaver *proxy,
    GCancellable *cancellable,
    GAsyncReadyCallback callback,
    gpointer user_data);

gboolean gsd_screen_saver_call_get_active_finish (
    GsdScreenSaver *proxy,
    gboolean *out_active,
    GAsyncResult *res,
    GError **error);

gboolean gsd_screen_saver_call_get_active_sync (
    GsdScreenSaver *proxy,
    gboolean *out_active,
    GCancellable *cancellable,
    GError **error);

void gsd_screen_saver_call_set_active (
    GsdScreenSaver *proxy,
    gboolean arg_value,
    GCancellable *cancellable,
    GAsyncReadyCallback callback,
    gpointer user_data);

gboolean gsd_screen_saver_call_set_active_finish (
    GsdScreenSaver *proxy,
    GAsyncResult *res,
    GError **error);

gboolean gsd_screen_saver_call_set_active_sync (
    GsdScreenSaver *proxy,
    gboolean arg_value,
    GCancellable *cancellable,
    GError **error);

void gsd_screen_saver_call_get_active_time (
    GsdScreenSaver *proxy,
    GCancellable *cancellable,
    GAsyncReadyCallback callback,
    gpointer user_data);

gboolean gsd_screen_saver_call_get_active_time_finish (
    GsdScreenSaver *proxy,
    guint *out_value,
    GAsyncResult *res,
    GError **error);

gboolean gsd_screen_saver_call_get_active_time_sync (
    GsdScreenSaver *proxy,
    guint *out_value,
    GCancellable *cancellable,
    GError **error);



/* ---- */

#define GSD_TYPE_SCREEN_SAVER_PROXY (gsd_screen_saver_proxy_get_type ())
#define GSD_SCREEN_SAVER_PROXY(o) (G_TYPE_CHECK_INSTANCE_CAST ((o), GSD_TYPE_SCREEN_SAVER_PROXY, GsdScreenSaverProxy))
#define GSD_SCREEN_SAVER_PROXY_CLASS(k) (G_TYPE_CHECK_CLASS_CAST ((k), GSD_TYPE_SCREEN_SAVER_PROXY, GsdScreenSaverProxyClass))
#define GSD_SCREEN_SAVER_PROXY_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), GSD_TYPE_SCREEN_SAVER_PROXY, GsdScreenSaverProxyClass))
#define GSD_IS_SCREEN_SAVER_PROXY(o) (G_TYPE_CHECK_INSTANCE_TYPE ((o), GSD_TYPE_SCREEN_SAVER_PROXY))
#define GSD_IS_SCREEN_SAVER_PROXY_CLASS(k) (G_TYPE_CHECK_CLASS_TYPE ((k), GSD_TYPE_SCREEN_SAVER_PROXY))

typedef struct _GsdScreenSaverProxy GsdScreenSaverProxy;
typedef struct _GsdScreenSaverProxyClass GsdScreenSaverProxyClass;
typedef struct _GsdScreenSaverProxyPrivate GsdScreenSaverProxyPrivate;

struct _GsdScreenSaverProxy
{
  /*< private >*/
  GDBusProxy parent_instance;
  GsdScreenSaverProxyPrivate *priv;
};

struct _GsdScreenSaverProxyClass
{
  GDBusProxyClass parent_class;
};

GType gsd_screen_saver_proxy_get_type (void) G_GNUC_CONST;

void gsd_screen_saver_proxy_new (
    GDBusConnection     *connection,
    GDBusProxyFlags      flags,
    const gchar         *name,
    const gchar         *object_path,
    GCancellable        *cancellable,
    GAsyncReadyCallback  callback,
    gpointer             user_data);
GsdScreenSaver *gsd_screen_saver_proxy_new_finish (
    GAsyncResult        *res,
    GError             **error);
GsdScreenSaver *gsd_screen_saver_proxy_new_sync (
    GDBusConnection     *connection,
    GDBusProxyFlags      flags,
    const gchar         *name,
    const gchar         *object_path,
    GCancellable        *cancellable,
    GError             **error);

void gsd_screen_saver_proxy_new_for_bus (
    GBusType             bus_type,
    GDBusProxyFlags      flags,
    const gchar         *name,
    const gchar         *object_path,
    GCancellable        *cancellable,
    GAsyncReadyCallback  callback,
    gpointer             user_data);
GsdScreenSaver *gsd_screen_saver_proxy_new_for_bus_finish (
    GAsyncResult        *res,
    GError             **error);
GsdScreenSaver *gsd_screen_saver_proxy_new_for_bus_sync (
    GBusType             bus_type,
    GDBusProxyFlags      flags,
    const gchar         *name,
    const gchar         *object_path,
    GCancellable        *cancellable,
    GError             **error);


/* ---- */

#define GSD_TYPE_SCREEN_SAVER_SKELETON (gsd_screen_saver_skeleton_get_type ())
#define GSD_SCREEN_SAVER_SKELETON(o) (G_TYPE_CHECK_INSTANCE_CAST ((o), GSD_TYPE_SCREEN_SAVER_SKELETON, GsdScreenSaverSkeleton))
#define GSD_SCREEN_SAVER_SKELETON_CLASS(k) (G_TYPE_CHECK_CLASS_CAST ((k), GSD_TYPE_SCREEN_SAVER_SKELETON, GsdScreenSaverSkeletonClass))
#define GSD_SCREEN_SAVER_SKELETON_GET_CLASS(o) (G_TYPE_INSTANCE_GET_CLASS ((o), GSD_TYPE_SCREEN_SAVER_SKELETON, GsdScreenSaverSkeletonClass))
#define GSD_IS_SCREEN_SAVER_SKELETON(o) (G_TYPE_CHECK_INSTANCE_TYPE ((o), GSD_TYPE_SCREEN_SAVER_SKELETON))
#define GSD_IS_SCREEN_SAVER_SKELETON_CLASS(k) (G_TYPE_CHECK_CLASS_TYPE ((k), GSD_TYPE_SCREEN_SAVER_SKELETON))

typedef struct _GsdScreenSaverSkeleton GsdScreenSaverSkeleton;
typedef struct _GsdScreenSaverSkeletonClass GsdScreenSaverSkeletonClass;
typedef struct _GsdScreenSaverSkeletonPrivate GsdScreenSaverSkeletonPrivate;

struct _GsdScreenSaverSkeleton
{
  /*< private >*/
  GDBusInterfaceSkeleton parent_instance;
  GsdScreenSaverSkeletonPrivate *priv;
};

struct _GsdScreenSaverSkeletonClass
{
  GDBusInterfaceSkeletonClass parent_class;
};

GType gsd_screen_saver_skeleton_get_type (void) G_GNUC_CONST;

GsdScreenSaver *gsd_screen_saver_skeleton_new (void);


G_END_DECLS

#endif /* __GSD_SCREEN_SAVER_GLUE_H__ */
