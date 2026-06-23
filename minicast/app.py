# MiniCast - a lightweight DLNA media renderer.

import os
import sys
import time
import logging
import threading
import gettext

import cherrypy
import pyperclip

from .gui import App, MenuItem, Platform
from .protocol import DLNAProtocol
from .server import Service
from .utils import SettingProperty, SETTING_DIR, Setting
from minicast_renderer.mpv import MPVRenderer

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
_ = gettext.gettext


class MiniCast(App):
    """MiniCast tray application.

    A minimal DLNA media renderer that uses mpv as the player.
    Cast videos / music / pictures from your phone to this computer.
    """
    if sys.platform == 'win32':
        ICON_MAP = ['assets/icon.ico',
                    'assets/menu_light_large.png',
                    'assets/menu_dark_large.png']
    else:
        ICON_MAP = ['assets/icon.png',
                    'assets/menu_light.png',
                    'assets/menu_dark.png']

    def __init__(self, lang=gettext.gettext):
        global _
        _ = lang
        # menu items
        self.toggle_menuitem = None
        self.quit_menuitem = None
        self.ip_menuitem = None
        self.version_menuitem = None
        self.start_at_login_menuitem = None
        self.menubar_icon_menuitem = None
        self.open_config_menuitem = None

        # setting items
        self.setting_start_at_login = None
        self.setting_menubar_icon = 0
        self.init_setting()

        # init service: MPV renderer + DLNA protocol are built-in
        self.service = Service(MPVRenderer(lang, Setting.mpv_default_path),
                               DLNAProtocol())

        icon_path = os.path.join(os.path.dirname(__file__),
                                 MiniCast.ICON_MAP[self.setting_menubar_icon])
        template = None if self.setting_menubar_icon == 0 else True
        self.copy_menuitem = None
        super(MiniCast, self).__init__("MiniCast",
                                       icon_path,
                                       self.build_app_menu(),
                                       template)
        cherrypy.engine.subscribe('start', self.service_start)
        cherrypy.engine.subscribe('stop', self.service_stop)
        cherrypy.engine.subscribe('renderer_start', self.renderer_start)
        cherrypy.engine.subscribe('renderer_av_stop', self.renderer_av_stop)
        cherrypy.engine.subscribe('renderer_av_uri', self.renderer_av_uri)
        cherrypy.engine.subscribe('ssdp_update_ip', self.update_service_ip)
        cherrypy.engine.subscribe('app_notify', self.notification)
        self.start_cast()
        logger.debug("MiniCast APP started")

    def build_app_menu(self):
        self.toggle_menuitem = MenuItem(_("Stop Cast"), self.on_toggle_service_click, key="p")
        self.quit_menuitem = MenuItem(_("Quit"), self.quit, key="q")
        # Settings are laid out directly in the top-level menu, grouped by
        # separators instead of being nested under a "Setting ▶" submenu.
        # Order: cast controls · status · player · preferences · quit.
        return [
            self.toggle_menuitem,
            None,
        ] + self.build_setting_menu() + [
            None,
            self.quit_menuitem,
        ]

    def build_setting_menu(self):
        ip_text = "/".join([ip for ip, _ in Setting.get_ip()])
        port = Setting.get_port()
        # Status block: app name + version on one line, listening address on the
        # next. Both are disabled (grey) read-only info lines.
        self.version_menuitem = MenuItem(
            "MiniCast v{}".format(Setting.get_version()), enabled=False)
        self.ip_menuitem = MenuItem(
            "{} · {}:{}".format(_("Listening"), ip_text, port), enabled=False)
        self.start_at_login_menuitem = MenuItem(_("Start At Login"),
                                                self.on_start_at_login_click,
                                                checked=self.setting_start_at_login)

        # Start-at-login only makes sense for a packaged app (not when running
        # from the python interpreter).
        platform_options = []
        if sys.platform == 'darwin' and sys.executable.endswith("Contents/MacOS/python"):
            platform_options = [self.start_at_login_menuitem]
            Setting.set_start_at_login(self.setting_start_at_login)
        elif sys.platform == 'win32' and "python" not in os.path.basename(sys.executable).lower():
            platform_options = [self.start_at_login_menuitem]
            Setting.set_start_at_login(self.setting_start_at_login)

        # appearance / menubar icon picker
        if sys.platform == 'darwin':
            self.menubar_icon_menuitem = MenuItem(_("Appearance"),
                                                  children=App.build_menu_item_group([
                                                      _("AppIcon"),
                                                      _("Pattern"),
                                                  ], self.on_menubar_icon_change_click))
        else:
            self.menubar_icon_menuitem = MenuItem(_("Appearance"),
                                                  children=App.build_menu_item_group([
                                                      _("AppIcon"),
                                                      _("PatternLight"),
                                                      _("PatternDark"),
                                                  ], self.on_menubar_icon_change_click))
        self.menubar_icon_menuitem.items()[self.setting_menubar_icon].checked = True

        self.open_config_menuitem = MenuItem(_("Open Config Directory"), self.on_open_config_click)

        player_settings = self.service.renderer.renderer_setting.build_menu()

        # Assemble the inline settings block. Each group is wrapped by a
        # separator so the top-level menu reads as distinct sections.
        status_block = [self.version_menuitem, self.ip_menuitem, None]
        player_block = player_settings + ([None] if len(player_settings) > 0 else [])
        preference_block = [self.menubar_icon_menuitem, self.open_config_menuitem] + \
            ([None] if platform_options else []) + platform_options

        return status_block + player_block + preference_block

    def init_setting(self):
        self.setting_start_at_login = Setting.get(SettingProperty.StartAtLogin, 0)
        self.setting_menubar_icon = Setting.get(SettingProperty.MenubarIcon,
                                                1 if sys.platform == 'darwin' else 0)

    def stop_cast(self):
        self.service.stop()

    def start_cast(self):
        self.service.run_async()

    # --- program event callbacks ---

    def update_service_status(self):
        if Setting.is_service_running():
            self.toggle_menuitem.text = _('Stop Cast')
        else:
            self.toggle_menuitem.text = _('Start Cast')
        self.update_menu()

    def service_start(self):
        """Called every time the DLNA service starts."""
        logger.info("service_start")
        if self.platform is Platform.Win32:
            msg = _("running at task bar")
        elif self.platform is Platform.Darwin:
            msg = _("running at menu bar")
        else:
            msg = _("running at desktop panel")
        if self.platform == Platform.Darwin:
            self.notification(_("MiniCast is hidden"), msg, sound=False)
        else:
            # pystray may fail to send notifications during early startup,
            # so wait a moment before notifying.
            threading.Thread(target=lambda: (
                time.sleep(2),
                self.notification(_("MiniCast is hidden"), msg, sound=False),
            )).start()
        self.update_service_status()

    def service_stop(self):
        """Called every time the DLNA service stops."""
        logger.info("service_stop")
        self.update_service_status()

    def update_service_ip(self):
        """Refresh the device address shown on the menu when IP/port changes."""
        logger.info("ssdp_update_ip")
        if self.ip_menuitem is not None:
            ip_text = "/".join([ip for ip, _ in Setting.get_ip()])
            port = Setting.get_port()
            self.ip_menuitem.text = "{} · {}:{}".format(_("Listening"), ip_text, port)
        self.version_menuitem.text = "MiniCast v{}".format(Setting.get_version())
        self.update_menu()

    def renderer_av_stop(self):
        logger.info("renderer_av_stop")
        if self.copy_menuitem:
            self.remove_menu_item_by_id(self.copy_menuitem.id)
        self.copy_menuitem = None

    def renderer_start(self):
        pass

    def renderer_av_uri(self, uri):
        logger.info("renderer_av_uri: " + uri)
        if self.copy_menuitem is not None:
            self.copy_menuitem.callback = lambda _: pyperclip.copy(uri)
            return
        self.copy_menuitem = MenuItem(
            _("Copy Video URI"),
            key="c",
            callback=lambda _: pyperclip.copy(uri))
        self.append_menu_item_after(self.toggle_menuitem.id, self.copy_menuitem)

    # --- menu click callbacks ---

    def on_open_config_click(self, item):
        self.open_directory(SETTING_DIR)

    def on_start_at_login_click(self, item):
        res = Setting.set_start_at_login(not item.checked)
        if res[0] == 0:
            item.checked = not item.checked
            Setting.set(SettingProperty.StartAtLogin,
                        1 if item.checked else 0)
        else:
            self.notification(_("Error"), _(res[1]))

    def on_toggle_service_click(self, item):
        if Setting.is_service_running():
            self.stop_cast()
        else:
            self.start_cast()

    def on_menubar_icon_change_click(self, item):
        for i in self.menubar_icon_menuitem.items():
            i.checked = False
        item.checked = True
        Setting.set(SettingProperty.MenubarIcon, item.data)
        icon_path = os.path.join(os.path.dirname(__file__), MiniCast.ICON_MAP[item.data])
        template = None if item.data == 0 else True
        self.update_icon(icon_path, template)

    def quit(self, item):
        if Setting.is_service_running():
            self.stop_cast()
        super(MiniCast, self).quit(item)


def gui(lang=gettext.gettext):
    """Launch MiniCast with the system tray UI."""
    MiniCast(lang).start()


def cli():
    """Launch MiniCast headless (no tray UI)."""
    Service(MPVRenderer(path=Setting.mpv_default_path), DLNAProtocol()).run()
