#!/usr/bin/env python3
"""Techy digital clock, drawn with Cairo, pinned to the desktop via gtk4-layer-shell."""

import datetime
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gtk4LayerShell, GLib, Gdk

FONT_FAMILY = "JetBrainsMono Nerd Font"
TIME_SIZE = 64
DATE_SIZE = 18
DATE_COLOR = (0.965, 0.757, 0.467)  # rose pine moon "gold"
BAR_COLOR = (0.918, 0.604, 0.592)   # rose pine moon "rose" (light pink)
GLOW_COLOR = (0.769, 0.655, 0.906)  # rose pine moon "iris" (purple)
TEXT = (0.878, 0.871, 0.957)        # rose pine moon "text" (off-white)
GLOW = 0.34                   # 0..1 glow strength behind the time
MARGIN_LEFT = 24              # aligned with hypr-quickmenu's LAYER_MARGIN_LEFT
MARGIN_BOTTOM = 666           # quickmenu's bottom margin (24) + its computed win_h (626px with the
                               # current 8 items/barHeight 70/barGap 6, skewAngle 4/extendDistance 20)
                               # + a 16px gap. Stale whenever quickmenu's item count/geometry changes --
                               # recompute win_w/win_h from config.json (see hypr-quickmenu's win_w/win_h
                               # calc) or check `hyprctl layers -j` (namespace "hypr-quickmenu") if the
                               # clock ever ends up overlapping it again.
WINDOW_WIDTH = 461             # matches hypr-quickmenu's computed win_w so right edges align
WINDOW_HEIGHT = 120


class ClockWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.BOTTOM)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, MARGIN_BOTTOM)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, MARGIN_LEFT)
        Gtk4LayerShell.set_exclusive_zone(self, -1)
        Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)

        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_decorated(False)

        area = Gtk.DrawingArea()
        area.set_content_width(WINDOW_WIDTH)
        area.set_content_height(WINDOW_HEIGHT)
        area.set_draw_func(self.on_draw)
        self.set_child(area)
        self.area = area

        # transparent background -- also strip decoration/border/shadow nodes,
        # since GTK4 can leave a thin border-ish line on an undecorated
        # layer-shell window even with the background itself transparent
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window, decoration {
                background: transparent;
                background-color: transparent;
                border: none;
                box-shadow: none;
                outline: none;
            }
            drawingarea {
                background: transparent;
                background-color: transparent;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        GLib.timeout_add(1000, self.tick)

    def tick(self):
        self.area.queue_draw()
        return True

    def on_draw(self, area, cr, w, h):
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%a %d %b").upper()

        cr.select_font_face(FONT_FAMILY, 0, 1)  # weight: bold
        cr.set_font_size(TIME_SIZE)
        x = 4
        y = h * 0.55

        # soft glow behind the time
        for i in range(6, 0, -1):
            alpha = GLOW * (i / 6) * 0.35
            cr.set_source_rgba(*GLOW_COLOR, alpha)
            cr.move_to(x, y)
            cr.set_font_size(TIME_SIZE + i)
            cr.show_text(time_str)

        # main time text
        cr.set_font_size(TIME_SIZE)
        cr.set_source_rgba(*TEXT, 0.95)
        cr.move_to(x, y)
        cr.show_text(time_str)

        # accent underline
        cr.set_source_rgba(*BAR_COLOR, 0.9)
        cr.set_line_width(2)
        cr.move_to(x, y + 8)
        cr.line_to(w - 4, y + 8)
        cr.stroke()

        # date, right-aligned, techy letter spacing via manual char draw
        cr.select_font_face(FONT_FAMILY, 0, 0)  # weight: normal
        cr.set_font_size(DATE_SIZE)
        spaced = " ".join(date_str)
        cr.set_source_rgba(*DATE_COLOR, 0.85)
        cr.move_to(4, y + 30)
        cr.show_text(spaced)


class ClockApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.chihin.cairoclock")

    def do_activate(self):
        win = ClockWindow()
        win.set_application(self)
        win.present()


if __name__ == "__main__":
    app = ClockApp()
    app.run(None)
