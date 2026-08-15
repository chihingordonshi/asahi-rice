#!/usr/bin/env python3
import gi

gi.require_version("Dbusmenu", "0.4")
gi.require_version("DbusmenuGtk3", "0.4")
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import DbusmenuGtk3, Gdk, Gtk, GtkLayerShell

NM_APPLET_BUS_NAME = "org.freedesktop.network-manager-applet"
NM_APPLET_MENU_PATH = "/org/ayatana/NotificationItem/nm_applet/Menu"


def main():
    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_decorated(False)
    window.set_default_size(1, 1)

    GtkLayerShell.init_for_window(window)
    GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, True)
    GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 36)
    GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, 80)
    GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.ON_DEMAND)

    window.show()
    while Gtk.events_pending():
        Gtk.main_iteration()

    menu = DbusmenuGtk3.Menu.new(NM_APPLET_BUS_NAME, NM_APPLET_MENU_PATH)
    menu.attach_to_widget(window, None)

    def quit(*_args):
        Gtk.main_quit()

    menu.connect("deactivate", quit)
    menu.connect("hide", quit)

    menu.show_all()
    menu.popup_at_widget(window, Gdk.Gravity.SOUTH_EAST, Gdk.Gravity.NORTH_EAST, None)

    Gtk.main()
    window.destroy()


if __name__ == "__main__":
    main()
