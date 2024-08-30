import re
from core.widgets.base import BaseWidget
from core.validation.widgets.yasb.language import VALIDATION_SCHEMA
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
import ctypes
import ctypes
from ctypes import wintypes

# Constants
LOCALE_NAME_MAX_LENGTH = 85
LOCALE_SISO639LANGNAME = 0x59
LOCALE_SISO3166CTRYNAME = 0x5A
LOCALE_SLANGUAGE = 0x2
LOCALE_SCOUNTRY = 0x6

# Define necessary ctypes structures and functions
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

class LanguageWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    def __init__(
        self,
        label: str,
        label_alt: str,
        update_interval: int,
        callbacks: dict[str, str],
    ):
        super().__init__(int(update_interval * 1000), class_name="language-widget")

        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt
 
        # Construct container
        self._widget_container_layout: QHBoxLayout = QHBoxLayout()
        self._widget_container_layout.setSpacing(0)
        self._widget_container_layout.setContentsMargins(0, 0, 0, 0)
        # Initialize container
        self._widget_container: QWidget = QWidget()
        self._widget_container.setLayout(self._widget_container_layout)
        self._widget_container.setProperty("class", "widget-container")
        # Add the container to the main widget layout
        self.widget_layout.addWidget(self._widget_container)

        self._create_dynamically_label(self._label_content, self._label_alt_content)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("update_label", self._update_label)

        self.callback_left = callbacks["on_left"]
        self.callback_right = callbacks["on_right"]
        self.callback_middle = callbacks["on_middle"]
        self.callback_timer = "update_label"

        self.start_timer()

    def _toggle_label(self):
        self._show_alt_label = not self._show_alt_label
        for widget in self._widgets:
            widget.setVisible(not self._show_alt_label)
        for widget in self._widgets_alt:
            widget.setVisible(self._show_alt_label)
        self._update_label()


    def _create_dynamically_label(self, content: str, content_alt: str):
        def process_content(content, is_alt=False):
            label_parts = re.split('(<span.*?>.*?</span>)', content) #Filters out empty parts before entering the loop
            label_parts = [part for part in label_parts if part]
            widgets = []
            for part in label_parts:
                part = part.strip()  # Remove any leading/trailing whitespace
                if not part:
                    continue
                if '<span' in part and '</span>' in part:
                    class_name = re.search(r'class=(["\'])([^"\']+?)\1', part)
                    class_result = class_name.group(2) if class_name else 'icon'
                    icon = re.sub(r'<span.*?>|</span>', '', part).strip()
                    label = QLabel(icon)
                    label.setProperty("class", class_result)
                else:
                    label = QLabel(part)
                    label.setProperty("class", "label") 
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)    
                self._widget_container_layout.addWidget(label)
                widgets.append(label)
                if is_alt:
                    label.setProperty("class", "label alt") 
                    label.hide()
                else:
                    label.show()
            return widgets
        self._widgets = process_content(content)
        self._widgets_alt = process_content(content_alt, is_alt=True)

        
    def _update_label(self):
        active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        label_parts = re.split('(<span.*?>.*?</span>)', active_label_content)
        label_parts = [part for part in label_parts if part]
        widget_index = 0
        try:
            lang = self._get_current_keyboard_language()
        except:
            lang = None
            
        for part in label_parts:
            part = part.strip()
            if part and widget_index < len(active_widgets) and isinstance(active_widgets[widget_index], QLabel):
                if '<span' in part and '</span>' in part:
                    # Ensure the icon is correctly set
                    icon = re.sub(r'<span.*?>|</span>', '', part).strip()
                    active_widgets[widget_index].setText(icon)
                else:
                    # Update label with formatted content
                    formatted_text = part.format(lang=lang) if lang else part
                    active_widgets[widget_index].setText(formatted_text)
                widget_index += 1

 
    # Get the current keyboard layout
    def _get_current_keyboard_language(self):
        # Get the foreground window (the active window)
        hwnd = user32.GetForegroundWindow()
        # Get the thread id of the foreground window
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        # Get the keyboard layout for the thread
        hkl = user32.GetKeyboardLayout(thread_id)
        # Get the language identifier from the HKL
        lang_id = hkl & 0xFFFF
        # Buffers for the language and country names
        lang_name = ctypes.create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
        country_name = ctypes.create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
        full_lang_name = ctypes.create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
        full_country_name = ctypes.create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
        # Get the ISO language name
        kernel32.GetLocaleInfoW(lang_id, LOCALE_SISO639LANGNAME, lang_name, LOCALE_NAME_MAX_LENGTH)
        # Get the ISO country name
        kernel32.GetLocaleInfoW(lang_id, LOCALE_SISO3166CTRYNAME, country_name, LOCALE_NAME_MAX_LENGTH)
        # Get the full language name
        kernel32.GetLocaleInfoW(lang_id, LOCALE_SLANGUAGE, full_lang_name, LOCALE_NAME_MAX_LENGTH)
        # Get the full country name
        kernel32.GetLocaleInfoW(lang_id, LOCALE_SCOUNTRY, full_country_name, LOCALE_NAME_MAX_LENGTH)
        
        language_code = lang_name.value
        country_code = country_name.value
        full_name = f"{full_lang_name.value}"
        return  {'language_code': language_code, 'country_code': country_code, 'full_name': full_name}
             
