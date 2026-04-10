import sys
import time
import json
import os
import socket
import struct
import threading
import queue

from PySide6.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout,
    QDialog, QFormLayout, QLineEdit, QPushButton, QCheckBox,
    QColorDialog, QSpinBox, QComboBox, QHBoxLayout, QMessageBox,
    QStyle, QProxyStyle
)
from PySide6.QtCore import QTimer, Qt, QRectF, QPointF, QEvent
from PySide6.QtGui import (
    QFont, QKeyEvent, QColor, QKeySequence, QShortcut,
    QFontDatabase, QImage, QPainter, QFontMetrics,
    QPainterPath, QPainterPathStroker, QPen
)

try:
    import SpoutGL
    import OpenGL.GL as GL
    SPOUT_AVAILABLE = True
except Exception:
    SPOUT_AVAILABLE = False


CONFIG_FILE = "counter_config.json"
OSC_PLAY_ADDRESS = "/9counter/play"
OSC_STOP_ADDRESS = "/9counter/stop"


def parse_time(t_str):
    parts = t_str.strip().split(":")
    if len(parts) != 4:
        raise ValueError("Time format must be HH:MM:SS:MS")

    h, m, s, ms = map(int, parts)

    if h < 0:
        raise ValueError("Hour must be >= 0")
    if not (0 <= m <= 59):
        raise ValueError("Minute must be 00~59")
    if not (0 <= s <= 59):
        raise ValueError("Second must be 00~59")
    if not (0 <= ms <= 999):
        raise ValueError("MS must be 000~999")

    return ((h * 3600 + m * 60 + s) * 1000) + ms


def format_time_for_input(ms):
    if ms < 0:
        ms = 0

    total_sec = ms // 1000
    ms_part = ms % 1000
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60

    return f"{h:02}:{m:02}:{s:02}:{ms_part:03}"


def format_time_for_display(ms, show_ms=False, continuous_hours=False):
    if ms < 0:
        ms = 0

    total_sec = ms // 1000
    ms_part = ms % 1000

    if continuous_hours:
        h = total_sec // 3600
    else:
        h = (total_sec // 3600) % 24

    m = (total_sec % 3600) // 60
    s = total_sec % 60

    if show_ms:
        return f"{h:02}:{m:02}:{s:02}.{ms_part:03}"
    return f"{h:02}:{m:02}:{s:02}"


def fit_font_size_for_rect(text, family, max_width, max_height, start_size):
    size = max(8, int(start_size))
    while size >= 8:
        font = QFont(family, size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferFullHinting)
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text)
        if text_rect.width() <= max_width and text_rect.height() <= max_height:
            return size
        size -= 1
    return 8


def get_local_ip_address():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def read_osc_string(data, offset):
    end = data.find(b"\x00", offset)
    if end == -1:
        raise ValueError("Invalid OSC string")
    text = data[offset:end].decode("utf-8", errors="ignore")
    next_offset = (end + 4) & ~0x03
    return text, next_offset


def extract_osc_address(packet):
    if not packet or packet[:1] != b"/":
        return None
    try:
        address, _ = read_osc_string(packet, 0)
        return address
    except Exception:
        return None


class OscServerThread(threading.Thread):
    def __init__(self, host, port, message_queue):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.message_queue = message_queue
        self.stop_event = threading.Event()
        self.sock = None
        self.last_error = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(0.2)

            while not self.stop_event.is_set():
                try:
                    data, _addr = self.sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except OSError:
                    break

                address = extract_osc_address(data)
                if address:
                    self.message_queue.put(address)
        except Exception as e:
            self.last_error = str(e)
        finally:
            if self.sock is not None:
                try:
                    self.sock.close()
                except Exception:
                    pass
            self.sock = None

    def stop(self):
        self.stop_event.set()
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass



class WhiteCheckBoxStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorCheckBox:
            rect = option.rect.adjusted(0, 0, -1, -1)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor("#aaaaaa"), 1))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(rect, 3, 3)

            if option.state & QStyle.State_On:
                pen = QPen(QColor("#111111"), 2)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)

                x1 = rect.left() + rect.width() * 0.22
                y1 = rect.top() + rect.height() * 0.55
                x2 = rect.left() + rect.width() * 0.43
                y2 = rect.top() + rect.height() * 0.75
                x3 = rect.left() + rect.width() * 0.78
                y3 = rect.top() + rect.height() * 0.28
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                painter.drawLine(QPointF(x2, y2), QPointF(x3, y3))
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("9Counter Settings")
        self.resize(900, 760)

        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: white; }
            QLineEdit, QComboBox {
                background-color: #3b3b3b;
                color: white;
                padding: 4px;
                border: 1px solid #555555;
            }
            QSpinBox {
                background-color: #3b3b3b;
                color: white;
                border: 1px solid #555555;
                padding-right: 20px;
                min-height: 24px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
                subcontrol-origin: border;
                background-color: #444444;
                border-left: 1px solid #555555;
            }
            QSpinBox::up-button { subcontrol-position: top right; }
            QSpinBox::down-button { subcontrol-position: bottom right; }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QPushButton {
                background-color: #555555;
                color: white;
                padding: 6px;
                border: 1px solid #666666;
            }
            QCheckBox {
                color: white;
                spacing: 8px;
            }
            QLabel { color: white; }
        """)

        self.setStyle(WhiteCheckBoxStyle(self.style()))

        layout = QVBoxLayout()
        top_row = QHBoxLayout()
        form = QFormLayout()

        self.use_start_checkbox = QCheckBox("Use Start Time")
        self.use_start_checkbox.setChecked(parent.use_start_time)

        self.start_input = QLineEdit(format_time_for_input(parent.start_time_ms))

        self.use_end_checkbox = QCheckBox("Use End Time")
        self.use_end_checkbox.setChecked(parent.use_end_time)

        self.end_input = QLineEdit(format_time_for_input(parent.end_time_ms))

        self.ms_checkbox = QCheckBox("Show MS")
        self.ms_checkbox.setChecked(parent.show_ms)

        self.continuous_hours_checkbox = QCheckBox("Continuous Hours (23 -> 24 -> 25...)")
        self.continuous_hours_checkbox.setChecked(parent.continuous_hours)

        self.top_checkbox = QCheckBox("Always on top")
        self.top_checkbox.setChecked(parent.always_on_top)

        self.borderless_checkbox = QCheckBox("Borderless")
        self.borderless_checkbox.setChecked(parent.borderless)

        self.font_combo = QComboBox()
        self.fixed_fonts = []
        db = QFontDatabase()
        for family in sorted(db.families()):
            if db.isFixedPitch(family):
                self.fixed_fonts.append(family)
        self.font_combo.addItems(self.fixed_fonts)

        idx = self.font_combo.findText(parent.font_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 300)
        self.font_size_spin.setValue(parent.font_size)

        self.text_color_btn = QPushButton("Select Text Color")
        self.bg_color_btn = QPushButton("Select Background Color")
        self.outline_color_btn = QPushButton("Select Outline Color")

        self.text_color_btn.clicked.connect(self.pick_text_color)
        self.bg_color_btn.clicked.connect(self.pick_bg_color)
        self.outline_color_btn.clicked.connect(self.pick_outline_color)

        self.text_color = QColor(parent.text_color)
        self.bg_color = QColor(parent.bg_color)
        self.outline_color = QColor(parent.outline_color)

        self.outline_checkbox = QCheckBox("Text Outline (Only Spout)")
        self.outline_checkbox.setChecked(parent.outline_enabled)

        self.outline_thickness_spin = QSpinBox()
        self.outline_thickness_spin.setRange(1, 20)
        self.outline_thickness_spin.setValue(parent.outline_thickness)

        self.win_w_spin = QSpinBox()
        self.win_w_spin.setRange(100, 5000)
        self.win_w_spin.setValue(parent.width())

        self.win_h_spin = QSpinBox()
        self.win_h_spin.setRange(100, 5000)
        self.win_h_spin.setValue(parent.height())

        self.win_x_spin = QSpinBox()
        self.win_x_spin.setRange(-5000, 5000)
        self.win_x_spin.setValue(parent.x())

        self.win_y_spin = QSpinBox()
        self.win_y_spin.setRange(-5000, 5000)
        self.win_y_spin.setValue(parent.y())

        self.spout_enabled_checkbox = QCheckBox("Enable Spout Output")
        self.spout_enabled_checkbox.setChecked(parent.spout_enabled)

        self.spout_alpha_checkbox = QCheckBox("Spout Transparent Background")
        self.spout_alpha_checkbox.setChecked(parent.spout_alpha)

        self.flip_fix_checkbox = QCheckBox("Flip Output")
        self.flip_fix_checkbox.setChecked(parent.spout_flip_fix)

        self.spout_name_input = QLineEdit(parent.spout_sender_name)

        self.spout_w_spin = QSpinBox()
        self.spout_w_spin.setRange(64, 7680)
        self.spout_w_spin.setValue(parent.spout_width)

        self.spout_h_spin = QSpinBox()
        self.spout_h_spin.setRange(64, 4320)
        self.spout_h_spin.setValue(parent.spout_height)

        self.osc_enabled_checkbox = QCheckBox("Enable OSC Input")
        self.osc_enabled_checkbox.setChecked(parent.osc_enabled)

        self.osc_port_spin = QSpinBox()
        self.osc_port_spin.setRange(1, 65535)
        self.osc_port_spin.setValue(parent.osc_input_port)

        self.osc_ip_label = QLabel(parent.local_ip_address)
        self.osc_ip_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        spout_status = "Installed" if SPOUT_AVAILABLE else "Not installed"
        self.spout_status_label = QLabel(f"SpoutGL : {spout_status}")

        form.addRow(self.use_start_checkbox)
        form.addRow("Start Time", self.start_input)
        form.addRow(self.use_end_checkbox)
        form.addRow("End Time", self.end_input)
        form.addRow(self.ms_checkbox)
        form.addRow(self.continuous_hours_checkbox)
        form.addRow(self.top_checkbox)
        form.addRow(self.borderless_checkbox)
        form.addRow("Font", self.font_combo)
        form.addRow("Font Size", self.font_size_spin)
        form.addRow("Text Color", self.text_color_btn)
        form.addRow("Background Color", self.bg_color_btn)
        form.addRow(self.outline_checkbox)
        form.addRow("Outline Thickness", self.outline_thickness_spin)
        form.addRow("Outline Color", self.outline_color_btn)
        form.addRow("Window Width", self.win_w_spin)
        form.addRow("Window Height", self.win_h_spin)
        form.addRow("Window X", self.win_x_spin)
        form.addRow("Window Y", self.win_y_spin)
        form.addRow(self.spout_enabled_checkbox)
        form.addRow(self.spout_alpha_checkbox)
        form.addRow(self.flip_fix_checkbox)
        form.addRow("Spout Sender Name", self.spout_name_input)
        form.addRow("Spout Width", self.spout_w_spin)
        form.addRow("Spout Height", self.spout_h_spin)
        form.addRow("Spout Status", self.spout_status_label)
        form.addRow(self.osc_enabled_checkbox)
        form.addRow("OSC Input Port", self.osc_port_spin)
        form.addRow("This PC IP", self.osc_ip_label)

        left_panel = QWidget()
        left_panel.setLayout(form)
        left_panel.setMinimumWidth(560)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        btn_row.addWidget(apply_btn)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(left_panel)
        left_layout.addLayout(btn_row)

        left_container = QWidget()
        left_container.setLayout(left_layout)

        shortcut_label = QLabel(
            "Shortcuts\n"
            "Space : Play / Pause\n"
            "S : Stop / Reset\n"
            "F : Fullscreen\n"
            "Esc : Exit Fullscreen\n"
            "F2 : Settings\n"
            "T : Always on top\n"
            "B : Borderless\n"
            "Ctrl+Q : Quit\n\n"
            "OSC Input\n"
            f"{OSC_PLAY_ADDRESS} : Play / Pause\n"
            f"{OSC_STOP_ADDRESS} : Stop / Reset\n\n"
            "S key behavior\n"
            "1st press : Back to Start Time\n"
            "2nd press : Reset to 00:00:00.000\n\n"
            "Spout Guide\n"
            "1. To use Spout output, you need an app that can receive Spout input.\n"
            "   (Arena, TouchDesigner, media server apps, etc.)\n\n"
            "2. If your PC has integrated/external GPU, set both the Spout sender\n"
            "   and receiver apps to the same GPU.\n"
            "   Windows Settings -> System -> Display -> Graphics\n"
            "   Add 9Counter as a desktop app and set GPU preference.\n"
            "   Do the same for the receiver app.\n\n"
            "3. If the output is upside down, enable Flip Output."
        )
        shortcut_label.setStyleSheet("color: #dddddd; padding-top: 4px;")
        shortcut_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        shortcut_label.setWordWrap(True)
        shortcut_label.setMinimumWidth(240)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(shortcut_label)
        right_layout.addStretch()

        right_container = QWidget()
        right_container.setLayout(right_layout)

        top_row.addWidget(left_container, 3)
        top_row.addWidget(right_container, 2)

        layout.addLayout(top_row)

        self.setLayout(layout)

    def pick_text_color(self):
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if color.isValid():
            self.text_color = color

    def pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color

    def pick_outline_color(self):
        color = QColorDialog.getColor(self.outline_color, self, "Select Outline Color")
        if color.isValid():
            self.outline_color = color

    def apply_settings(self):
        try:
            new_use_start = self.use_start_checkbox.isChecked()
            new_use_end = self.use_end_checkbox.isChecked()

            new_start_ms = parse_time(self.start_input.text())
            new_end_ms = parse_time(self.end_input.text())

            if not new_use_start:
                new_start_ms = 0

            if new_use_end and new_end_ms < new_start_ms:
                QMessageBox.warning(self, "Error", "End Time must be greater than or equal to Start Time.")
                return

            self.parent.use_start_time = new_use_start
            self.parent.use_end_time = new_use_end
            self.parent.start_time_ms = new_start_ms
            self.parent.end_time_ms = new_end_ms
            self.parent.show_ms = self.ms_checkbox.isChecked()
            self.parent.continuous_hours = self.continuous_hours_checkbox.isChecked()

            self.parent.font_family = self.font_combo.currentText()
            self.parent.font_size = self.font_size_spin.value()
            self.parent.text_color = self.text_color.name()
            self.parent.bg_color = self.bg_color.name()
            self.parent.outline_enabled = self.outline_checkbox.isChecked()
            self.parent.outline_thickness = self.outline_thickness_spin.value()
            self.parent.outline_color = self.outline_color.name()

            self.parent.saved_window_x = self.win_x_spin.value()
            self.parent.saved_window_y = self.win_y_spin.value()
            self.parent.saved_window_w = self.win_w_spin.value()
            self.parent.saved_window_h = self.win_h_spin.value()

            self.parent.spout_enabled = self.spout_enabled_checkbox.isChecked()
            self.parent.spout_alpha = self.spout_alpha_checkbox.isChecked()
            self.parent.spout_flip_fix = self.flip_fix_checkbox.isChecked()
            self.parent.spout_sender_name = self.spout_name_input.text().strip() or "9Counter"
            self.parent.spout_width = self.spout_w_spin.value()
            self.parent.spout_height = self.spout_h_spin.value()

            self.parent.osc_enabled = self.osc_enabled_checkbox.isChecked()
            self.parent.osc_input_port = self.osc_port_spin.value()
            self.parent.local_ip_address = get_local_ip_address()

            self.parent.invalidate_spout_font_cache()
            self.parent.apply_display_style()
            self.parent.resize(self.parent.saved_window_w, self.parent.saved_window_h)
            self.parent.move(self.parent.saved_window_x, self.parent.saved_window_y)

            if self.top_checkbox.isChecked() != self.parent.always_on_top:
                self.parent.toggle_always_on_top()

            if self.borderless_checkbox.isChecked() != self.parent.borderless:
                self.parent.toggle_borderless()

            self.parent.reset_spout_sender()
            self.parent.reset_osc_server()
            self.parent.stop_stage = 0
            self.parent.stop()
            self.parent.save_config()
            self.close()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid setting.\n{e}")


class TimerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.use_start_time = False
        self.use_end_time = False
        self.start_time_ms = 0
        self.end_time_ms = 3600000

        self.running = False
        self.base_elapsed = 0
        self.start_perf = 0.0
        self.last_perf_counter = 0.0

        self.show_ms = False
        self.continuous_hours = False

        self.always_on_top = False
        self.borderless = False

        self.font_family = "Consolas"
        self.font_size = 80
        self.text_color = "#ffffff"
        self.bg_color = "#000000"

        self.outline_enabled = True
        self.outline_color = "#000000"
        self.outline_thickness = 4

        self.saved_window_x = 100
        self.saved_window_y = 100
        self.saved_window_w = 1000
        self.saved_window_h = 320

        self.zero_reset_mode = False
        self.stop_stage = 0

        self.spout_enabled = False
        self.spout_alpha = True
        self.spout_flip_fix = False
        self.spout_sender_name = "9Counter"
        self.spout_width = 1280
        self.spout_height = 720
        self.spout_sender = None
        self.spout_error = None

        self.osc_enabled = False
        self.osc_input_port = 8000
        self.local_ip_address = get_local_ip_address()
        self.osc_thread = None
        self.osc_queue = queue.Queue()
        self.osc_error = None

        self.spout_cached_font_size = None
        self.spout_cache_key = None
        self.spout_last_text = None
        self.spout_last_image = None

        self.label = QLabel("00:00:00")
        self.label.setAlignment(Qt.AlignCenter)

        self.spout_status_label = QLabel(self.spout_sender_name, self)
        self.spout_status_label.setStyleSheet("""
            QLabel {
                color: #00ff66;
                background-color: rgba(0, 40, 0, 180);
                border: 1px solid #00aa44;
                padding: 2px 6px;
                font-size: 10pt;
                font-weight: bold;
            }
        """)
        self.spout_status_label.hide()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.update_window_title()

        self.load_config()
        self.resize(self.saved_window_w, self.saved_window_h)
        self.move(self.saved_window_x, self.saved_window_y)

        self.apply_display_style()
        self.reset_spout_sender()
        self.reset_osc_server()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(16)

        self.osc_poll_timer = QTimer()
        self.osc_poll_timer.timeout.connect(self.process_osc_messages)
        self.osc_poll_timer.start(20)

        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.close)

        self.last_perf_counter = time.perf_counter()
        self.update_display()
        self.update_spout_indicator()
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self and event.type() in {
            QEvent.WindowStateChange,
            QEvent.ActivationChange,
            QEvent.Move,
            QEvent.Resize,
        }:
            self.sync_elapsed_from_perf()
        return super().eventFilter(obj, event)

    def sync_elapsed_from_perf(self):
        now = time.perf_counter()
        if self.running:
            delta_ms = int((now - self.last_perf_counter) * 1000)
            if delta_ms > 0:
                self.base_elapsed += delta_ms
                self.start_perf = now
        self.last_perf_counter = now

    def invalidate_spout_font_cache(self):
        self.spout_cached_font_size = None
        self.spout_cache_key = None
        self.spout_last_text = None
        self.spout_last_image = None

    def get_spout_sample_text(self):
        if self.show_ms:
            return "88:88:88.888"
        return "88:88:88"

    def update_window_title(self):
        sender = (self.spout_sender_name or "").strip()
        if sender and sender != "9Counter":
            self.setWindowTitle(f"9Counter-{sender}")
        else:
            self.setWindowTitle("9Counter")

    def update_spout_indicator(self):
        label_text = (self.spout_sender_name or "").strip() or "9Counter"
        self.spout_status_label.setText(label_text)
        self.spout_status_label.adjustSize()
        if self.spout_enabled and SPOUT_AVAILABLE:
            self.spout_status_label.show()
            self.spout_status_label.raise_()
            self.spout_status_label.move(8, 8)
        else:
            self.spout_status_label.hide()

    def get_display_font(self):
        font = QFont(self.font_family, self.font_size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferFullHinting)
        font.setKerning(False)
        font.setLetterSpacing(QFont.PercentageSpacing, 100)
        return font

    def apply_display_style(self):
        self.label.setFont(self.get_display_font())
        self.label.setStyleSheet(
            f"color: {self.text_color};"
            f"background-color: {self.bg_color};"
            f"margin: 0px;"
            f"padding: 0px;"
            f"border: none;"
        )
        self.setStyleSheet(
            f"background-color: {self.bg_color};"
            f"border: none;"
        )
        self.invalidate_spout_font_cache()
        self.update_window_title()
        self.update_display()
        self.update_spout_indicator()

    def get_elapsed_ms(self):
        if self.running:
            return self.base_elapsed + int((time.perf_counter() - self.last_perf_counter) * 1000)
        return self.base_elapsed

    def get_current_base_start(self):
        if self.zero_reset_mode:
            return 0
        return self.start_time_ms if self.use_start_time else 0

    def get_current_time_ms(self):
        return self.get_current_base_start() + self.get_elapsed_ms()

    def get_display_text(self):
        return format_time_for_display(
            self.get_current_time_ms(),
            self.show_ms,
            self.continuous_hours,
        )

    def update_display(self):
        self.label.setText(self.get_display_text())

    def update_time(self):
        self.sync_elapsed_from_perf()
        current = self.get_current_time_ms()

        if self.use_end_time and current >= self.end_time_ms:
            current = self.end_time_ms
            self.running = False
            base_start = self.get_current_base_start()
            self.base_elapsed = max(0, self.end_time_ms - base_start)

        self.label.setText(
            format_time_for_display(current, self.show_ms, self.continuous_hours)
        )

        if self.spout_enabled:
            self.send_spout_frame()

    def play(self):
        if self.use_end_time and self.get_current_time_ms() >= self.end_time_ms:
            return

        if not self.running:
            self.running = True
            self.start_perf = time.perf_counter()
            self.last_perf_counter = self.start_perf
            self.stop_stage = 0

    def pause(self):
        if self.running:
            self.base_elapsed += int((time.perf_counter() - self.last_perf_counter) * 1000)
            self.running = False
            self.last_perf_counter = time.perf_counter()

    def toggle_play_pause(self):
        if self.running:
            self.pause()
        else:
            self.play()

    def stop(self):
        self.running = False
        self.last_perf_counter = time.perf_counter()

        if self.stop_stage == 0:
            self.zero_reset_mode = False
            self.base_elapsed = 0
            self.stop_stage = 1
        else:
            self.zero_reset_mode = True
            self.base_elapsed = 0
            self.stop_stage = 0

        self.update_display()
        if self.spout_enabled:
            self.send_spout_frame()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self.update_spout_indicator()

    def toggle_borderless(self):
        self.borderless = not self.borderless
        self.setWindowFlag(Qt.FramelessWindowHint, self.borderless)
        self.show()
        self.apply_display_style()

    def open_settings(self):
        self.sync_elapsed_from_perf()
        self.local_ip_address = get_local_ip_address()
        dlg = SettingsDialog(self)
        dlg.exec()
        self.last_perf_counter = time.perf_counter()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.toggle_play_pause()

        elif event.key() == Qt.Key_S:
            self.stop()

        elif event.key() == Qt.Key_F:
            self.showFullScreen()
            self.update_spout_indicator()

        elif event.key() == Qt.Key_Escape:
            self.showNormal()
            self.update_spout_indicator()

        elif event.key() == Qt.Key_F2:
            self.open_settings()

        elif event.key() == Qt.Key_T:
            self.toggle_always_on_top()

        elif event.key() == Qt.Key_B:
            self.toggle_borderless()

        elif event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()

    def process_osc_messages(self):
        while True:
            try:
                address = self.osc_queue.get_nowait()
            except queue.Empty:
                break

            if address == OSC_PLAY_ADDRESS:
                self.toggle_play_pause()
            elif address == OSC_STOP_ADDRESS:
                self.stop()

    def stop_osc_server(self):
        if self.osc_thread is not None:
            self.osc_thread.stop()
            self.osc_thread.join(timeout=0.5)
            self.osc_thread = None

        while True:
            try:
                self.osc_queue.get_nowait()
            except queue.Empty:
                break

    def reset_osc_server(self):
        self.stop_osc_server()
        self.osc_error = None

        if not self.osc_enabled:
            return

        self.local_ip_address = get_local_ip_address()
        self.osc_thread = OscServerThread("0.0.0.0", self.osc_input_port, self.osc_queue)
        self.osc_thread.start()

    def build_centered_text_path(self, painter, draw_rect, text):
        metrics = painter.fontMetrics()
        text_rect = metrics.horizontalAdvance(text)

        x = draw_rect.x() + (draw_rect.width() - text_rect) / 2
        y = draw_rect.y() + (draw_rect.height() + metrics.ascent() - metrics.descent()) / 2

        path = QPainterPath()
        path.addText(QPointF(x, y), painter.font(), text)
        return path

    def render_spout_image(self):
        text = self.get_display_text()
        if self.spout_last_text == text and self.spout_last_image is not None:
            return self.spout_last_image

        image = QImage(self.spout_width, self.spout_height, QImage.Format_RGBA8888)

        if self.spout_alpha:
            image.fill(Qt.transparent)
        else:
            image.fill(QColor(self.bg_color))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Base flip is enabled by default so first launch appears upright
        painter.translate(0, self.spout_height)
        painter.scale(1, -1)

        # Optional extra flip for systems that still appear upside down
        if self.spout_flip_fix:
            painter.translate(0, self.spout_height)
            painter.scale(1, -1)

        margin_x = int(self.spout_width * 0.04)
        margin_y = int(self.spout_height * 0.08)
        draw_rect = QRectF(
            margin_x,
            margin_y,
            self.spout_width - (margin_x * 2),
            self.spout_height - (margin_y * 2),
        )

        safe_outline = max(0, self.outline_thickness if self.outline_enabled else 0)
        fit_width = max(10, int(draw_rect.width()) - safe_outline * 4)
        fit_height = max(10, int(draw_rect.height()) - safe_outline * 4)

        cache_key = (
            self.spout_width,
            self.spout_height,
            self.font_family,
            self.show_ms,
            self.outline_enabled,
            self.outline_thickness,
        )

        if self.spout_cached_font_size is None or self.spout_cache_key != cache_key:
            start_font_size = int(self.spout_height * 0.45)
            fitted_size = fit_font_size_for_rect(
                text=self.get_spout_sample_text(),
                family=self.font_family,
                max_width=fit_width,
                max_height=fit_height,
                start_size=start_font_size,
            )
            self.spout_cached_font_size = fitted_size
            self.spout_cache_key = cache_key

        font = QFont(self.font_family, self.spout_cached_font_size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferFullHinting)
        font.setKerning(False)
        font.setLetterSpacing(QFont.PercentageSpacing, 100)
        painter.setFont(font)

        text_path = self.build_centered_text_path(painter, draw_rect, text)

        if self.outline_enabled and self.outline_thickness > 0:
            stroker = QPainterPathStroker()
            stroker.setWidth(self.outline_thickness * 2.0)
            stroker.setJoinStyle(Qt.RoundJoin)
            stroke_path = stroker.createStroke(text_path)
            painter.fillPath(stroke_path, QColor(self.outline_color))

        painter.fillPath(text_path, QColor(self.text_color))
        painter.end()

        self.spout_last_text = text
        self.spout_last_image = image
        return image

    def reset_spout_sender(self):
        self.spout_sender = None
        self.spout_error = None
        self.spout_last_text = None
        self.spout_last_image = None

        if not self.spout_enabled:
            self.update_spout_indicator()
            return

        if not SPOUT_AVAILABLE:
            self.spout_error = "SpoutGL not installed"
            self.update_spout_indicator()
            return

        try:
            self.spout_sender = SpoutGL.SpoutSender()
            self.spout_sender.setSenderName(self.spout_sender_name)
        except Exception as e:
            self.spout_sender = None
            self.spout_error = str(e)

        self.update_spout_indicator()

    def send_spout_frame(self):
        if not self.spout_enabled:
            return
        if not SPOUT_AVAILABLE:
            return
        if self.spout_sender is None:
            self.reset_spout_sender()
            if self.spout_sender is None:
                return

        try:
            image = self.render_spout_image()
            ptr = image.bits()
            frame_bytes = bytes(ptr)

            self.spout_sender.sendImage(
                frame_bytes,
                self.spout_width,
                self.spout_height,
                GL.GL_RGBA,
                True,
                0,
            )
        except Exception as e:
            self.spout_error = str(e)

    def moveEvent(self, event):
        self.sync_elapsed_from_perf()
        super().moveEvent(event)
        if not self.isFullScreen():
            self.saved_window_x = self.x()
            self.saved_window_y = self.y()

    def resizeEvent(self, event):
        self.sync_elapsed_from_perf()
        super().resizeEvent(event)
        if not self.isFullScreen():
            self.saved_window_w = self.width()
            self.saved_window_h = self.height()
        self.update_spout_indicator()

    def save_config(self):
        data = {
            "use_start_time": self.use_start_time,
            "use_end_time": self.use_end_time,
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "show_ms": self.show_ms,
            "continuous_hours": self.continuous_hours,
            "always_on_top": self.always_on_top,
            "borderless": self.borderless,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "bg_color": self.bg_color,
            "outline_enabled": self.outline_enabled,
            "outline_color": self.outline_color,
            "outline_thickness": self.outline_thickness,
            "saved_window_x": self.saved_window_x,
            "saved_window_y": self.saved_window_y,
            "saved_window_w": self.saved_window_w,
            "saved_window_h": self.saved_window_h,
            "spout_enabled": self.spout_enabled,
            "spout_alpha": self.spout_alpha,
            "spout_flip_fix": self.spout_flip_fix,
            "spout_sender_name": self.spout_sender_name,
            "spout_width": self.spout_width,
            "spout_height": self.spout_height,
            "osc_enabled": self.osc_enabled,
            "osc_input_port": self.osc_input_port,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.use_start_time = data.get("use_start_time", self.use_start_time)
            self.use_end_time = data.get("use_end_time", self.use_end_time)
            self.start_time_ms = data.get("start_time_ms", self.start_time_ms)
            self.end_time_ms = data.get("end_time_ms", self.end_time_ms)
            self.show_ms = data.get("show_ms", self.show_ms)
            self.continuous_hours = data.get("continuous_hours", self.continuous_hours)
            self.always_on_top = data.get("always_on_top", self.always_on_top)
            self.borderless = data.get("borderless", self.borderless)
            self.font_family = data.get("font_family", self.font_family)
            self.font_size = data.get("font_size", self.font_size)
            self.text_color = data.get("text_color", self.text_color)
            self.bg_color = data.get("bg_color", self.bg_color)
            self.outline_enabled = data.get("outline_enabled", self.outline_enabled)
            self.outline_color = data.get("outline_color", self.outline_color)
            self.outline_thickness = data.get("outline_thickness", self.outline_thickness)
            self.saved_window_x = data.get("saved_window_x", self.saved_window_x)
            self.saved_window_y = data.get("saved_window_y", self.saved_window_y)
            self.saved_window_w = data.get("saved_window_w", self.saved_window_w)
            self.saved_window_h = data.get("saved_window_h", self.saved_window_h)
            self.spout_enabled = data.get("spout_enabled", self.spout_enabled)
            self.spout_alpha = data.get("spout_alpha", self.spout_alpha)
            self.spout_flip_fix = data.get("spout_flip_fix", self.spout_flip_fix)
            self.spout_sender_name = data.get("spout_sender_name", self.spout_sender_name)
            self.spout_width = data.get("spout_width", self.spout_width)
            self.spout_height = data.get("spout_height", self.spout_height)
            self.osc_enabled = data.get("osc_enabled", self.osc_enabled)
            self.osc_input_port = data.get("osc_input_port", self.osc_input_port)
            self.local_ip_address = get_local_ip_address()
        except Exception:
            pass

    def closeEvent(self, event):
        self.save_config()
        self.stop_osc_server()
        self.spout_sender = None
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()

    if window.always_on_top:
        window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    if window.borderless:
        window.setWindowFlag(Qt.FramelessWindowHint, True)

    window.show()
    sys.exit(app.exec())
