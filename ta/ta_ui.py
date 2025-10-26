"""
project : DTD - ta_ui.py v2.0.0
Optimized with dirty tracking and better resource management
"""

import sys, utime
import st7789
import ta_config as config
from ta_logger import get_logger

logger = get_logger()

if "utils" not in sys.path:
    sys.path.append("utils")

import tft_config
import vga1_8x16 as font

class UI:
    C_BLACK = config.COLORS["C_BLACK"]
    C_WHITE = config.COLORS["C_WHITE"]
    C_BG = config.COLORS["C_BG"]
    C_HDR = config.COLORS["C_HDR"]
    C_STS = config.COLORS["C_STS"]
    C_ERR = config.COLORS["C_ERR"]
    C_WARN = config.COLORS["C_WARN"]
    C_ON = config.COLORS["C_ON"]
    C_OFF = config.COLORS["C_OFF"]
    C_UNK = config.COLORS["C_UNK"]
    C_BOX = config.COLORS["C_BOX"]

    def __init__(self, rotation=1, buffer_size=64*64*2, bl_gpio=None, bl_percent=85, group_labels=None):
        self.tft = tft_config.config(rotation, buffer_size=buffer_size)
        self._init_done = False
        self.init()

        self.W = int(self.tft.width())
        self.H = int(self.tft.height())
        self.FW = getattr(font, "WIDTH", 8)
        self.FH = getattr(font, "HEIGHT", 16)
        self.PAD = config.UI["PAD"]
        self.HEADER_H = config.UI["HEADER_H"]
        self.STATUS_H = config.UI["STATUS_BAR_H"]

        self.IND_Y = self.HEADER_H + 2
        self.IND_H = config.UI["IND_H"]
        self.PROGRESS_EXTRA_GAP = max(0, self.IND_H + 2)
        self.CONTENT_Y = self.HEADER_H + self.PAD + self.PROGRESS_EXTRA_GAP

        self.LOG_MAX = 6
        self.log_buf = []

        self.group_count = 5
        self.groups = [{"label": f"G{i+1}", "state": None, "battery": 100, "rssi": 0} for i in range(self.group_count)]
        if group_labels:
            self.set_groups(group_labels)
        self._layout_groups()

        # Dirty tracking
        self._dirty_tracking = config.UI.get("DIRTY_TRACKING", True)
        self._group_states_cache = [None] * self.group_count
        self._dirty_groups = set()

        if bl_gpio is not None:
            try:
                self.set_backlight_gpio(bl_gpio, bl_percent)
            except Exception:
                pass

        self.clear(self.C_BG)
        self.header(config.MAIN["APP_NAME"])
        self._indicator_clear()
        self.status("Prêt")
        self.show_groups()
        self.message("En attente…", y=self.grp_bottom + self.PAD)
        
        logger.info("UI initialisée ({}x{})".format(self.W, self.H), "ui")

    def init(self):
        if not self._init_done:
            self.tft.init()
            utime.sleep_ms(20)
            self._init_done = True

    def deinit(self):
        if self._init_done:
            self.tft.deinit()
            self._init_done = False

    def clear(self, color=None):
        self.tft.fill(self.C_BG if color is None else color)

    def _text(self, s, x, y, fg=None, bg=None):
        fg = self.C_WHITE if fg is None else fg
        bg = self.C_BG if bg is None else bg
        self.tft.text(font, str(s), int(x), int(y), fg, bg)

    def _text_center(self, s, cx, y, fg=None, bg=None):
        s = str(s)
        w = self.FW * len(s)
        self._text(s, max(0, int(cx - w//2)), int(y), fg, bg)

    def _frame(self, x, y, w, h, color):
        self.tft.fill_rect(x, y, w, 1, color)
        self.tft.fill_rect(x, y+h-1, w, 1, color)
        self.tft.fill_rect(x, y, 1, h, color)
        self.tft.fill_rect(x+w-1, y, 1, h, color)

    def _fit_text(self, s, max_px):
        s = str(s)
        if self.FW * len(s) <= max_px:
            return s
        max_chars = max(1, (max_px // self.FW) - 1)
        return (s[:max_chars] + "…")

    def header(self, text, bg=None, fg=None, show_version=True):
        bg = self.C_HDR if bg is None else bg
        fg = self.C_WHITE if fg is None else fg
        self.tft.fill_rect(0, 0, self.W, self.HEADER_H, bg)

        display = str(text)
        if show_version:
            display = "{} (v{})".format(display, config.MAIN["VERSION_NO"])

        max_px = self.W - 2 * self.PAD
        display = self._fit_text(display, max_px)
        self._text(display, self.PAD, 4, fg, bg)

    def status(self, text, bg=None, fg=None):
        bg = self.C_STS if bg is None else bg
        fg = self.C_BLACK if fg is None else fg
        y = self.H - self.STATUS_H
        self.tft.fill_rect(0, y, self.W, self.STATUS_H, bg)
        self._text(text, self.PAD, y + 3, fg, bg)

    def message(self, text, y=None, fg=None, bg=None):
        if y is None:
            y = self.H - self.STATUS_H - (self.FH * 2)
        self._text(text, self.PAD, y, fg, bg)

    def _layout_groups(self):
        self.grp_h = self.FH * 3 + 8
        self.grp_y = self.CONTENT_Y
        self.grp_bottom = self.grp_y + self.grp_h + self.PAD
        gap = 4
        usable_w = self.W - 2*self.PAD
        box_w = (usable_w - (self.group_count - 1) * gap) // self.group_count
        self.grp_boxes = []
        x = self.PAD
        for _ in range(self.group_count):
            self.grp_boxes.append((x, self.grp_y, box_w, self.grp_h))
            x += box_w + gap

    def set_groups(self, labels):
        n = min(len(labels), self.group_count)
        for i in range(n):
            self.groups[i]["label"] = str(labels[i])
        self.show_groups()

    def _state_color(self, state):
        if state in (True, "on", "ON", 1):
            return self.C_ON
        if state in (False, "off", "OFF", 0):
            return self.C_OFF
        return self.C_UNK

    def update_group(self, index, state=None, label=None, battery=None, rssi=None):
        if not (0 <= index < self.group_count):
            return
        
        changed = False
        
        if label is not None and self.groups[index]["label"] != label:
            self.groups[index]["label"] = str(label)
            changed = True
        
        if state is not None and self._group_states_cache[index] != state:
            self.groups[index]["state"] = state
            self._group_states_cache[index] = state
            changed = True
        
        if battery is not None:
            self.groups[index]["battery"] = battery
            changed = True
        
        if rssi is not None:
            self.groups[index]["rssi"] = rssi
            changed = True
        
        if changed:
            if self._dirty_tracking:
                self._dirty_groups.add(index)
            else:
                self._draw_group(index)

    def show_groups(self):
        for i in range(self.group_count):
            self._draw_group(i)

    def render_dirty(self):
        """Rafraîchit uniquement les groupes modifiés"""
        for i in self._dirty_groups:
            self._draw_group(i)
        self._dirty_groups.clear()

    def _draw_group(self, i):
        x, y, w, h = self.grp_boxes[i]
        g = self.groups[i]
        label = g["label"]
        state = g["state"]
        col = self._state_color(state)

        self.tft.fill_rect(x, y, w, h, self.C_BG)
        self._frame(x, y, w, h, self.C_BOX)

        self.tft.fill_rect(x+1, y+1, w-2, self.FH, col)

        cx = x + w//2
        label_fit = self._fit_text(label, w - 6)
        self._text_center(label_fit, cx, y + self.FH + 4, self.C_WHITE, self.C_BG)

        stxt = "ON" if col == self.C_ON else ("OFF" if col == self.C_OFF else "UNK")
        self._text_center(stxt, cx, y + h - self.FH - 2, self.C_WHITE, self.C_BG)

    def log_add(self, line):
        self.log_buf.append(str(line))
        if len(self.log_buf) > self.LOG_MAX:
            self.log_buf = self.log_buf[-self.LOG_MAX:]
        self.log_draw()

    def log_draw(self):
        top = self.grp_bottom
        bottom = self.H - self.STATUS_H - 4
        zone_h = max(0, bottom - top)
        self.tft.fill_rect(0, top, self.W, zone_h, self.C_BG)

        y = top
        line_h = self.FH + 1
        max_lines = zone_h // line_h
        lines_to_show = self.log_buf[-max_lines:] if len(self.log_buf) > max_lines else self.log_buf
        for s in lines_to_show:
            self._text(s, self.PAD, y, self.C_WHITE, self.C_BG)
            y += line_h

    def _indicator_clear(self):
        self.tft.fill_rect(0, self.IND_Y, self.W, self.IND_H, self.C_BLACK)

    def _indicator_draw_for_group(self, group_index, color=None):
        if not (1 <= group_index <= self.group_count):
            self._indicator_clear()
            return
        i = group_index - 1
        x, y, w, h = self.grp_boxes[i]
        band_x = x + 1
        band_w = w - 2
        band_color = self.C_ON if color is None else color

        self._indicator_clear()
        self.tft.fill_rect(band_x, self.IND_Y, band_w, self.IND_H, band_color)
        self._frame(band_x, self.IND_Y, band_w, self.IND_H, self.C_BLACK)

    def progress(self, percent=None, text=None, color=None):
        if isinstance(percent, int) and (1 <= percent <= self.group_count):
            self._indicator_draw_for_group(percent, color=color)
        else:
            self._indicator_clear()

    def toast(self, text, ms=1200, bg=None, fg=None):
        bg = self.C_WARN if bg is None else bg
        fg = self.C_BLACK if fg is None else fg
        w = self.FW * len(str(text)) + 10
        h = self.FH + 6
        x = max(2, self.W//2 - w//2)
        y = self.H - self.STATUS_H - h - 4
        self.tft.fill_rect(x, y, w, h, bg)
        self._frame(x, y, w, h, self.C_BLACK)
        self._text(text, x+5, y+3, fg, bg)
        utime.sleep_ms(int(ms))
        self.tft.fill_rect(x, y, w, h, self.C_BG)

    def set_backlight_gpio(self, gpio=38, percent=100, freq=1000):
        from machine import Pin, PWM
        pct = max(0, min(100, int(percent)))
        pwm = PWM(Pin(gpio, Pin.OUT), freq=freq)
        pwm.duty_u16(int(pct * 65535 // 100))
        return pwm

logger.info("ta_ui.py v2.0.0 chargé", "ui")
