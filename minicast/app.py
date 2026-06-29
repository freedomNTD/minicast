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
        self.rename_menuitem = None
        self.copy_menuitem = None
        # progress / recent blocks are built lazily while casting
        self.progress_menuitem = None
        self.recent_menuitem = None

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
        super(MiniCast, self).__init__("MiniCast",
                                       icon_path,
                                       self.build_app_menu(),
                                       template)
        cherrypy.engine.subscribe('start', self.service_start)
        cherrypy.engine.subscribe('stop', self.service_stop)
        cherrypy.engine.subscribe('renderer_start', self.renderer_start)
        cherrypy.engine.subscribe('renderer_av_stop', self.renderer_av_stop)
        cherrypy.engine.subscribe('renderer_av_uri', self.renderer_av_uri)
        cherrypy.engine.subscribe('mpv_update_progress', self.on_mpv_progress)
        cherrypy.engine.subscribe('ssdp_update_ip', self.update_service_ip)
        cherrypy.engine.subscribe('app_notify', self.notification)
        self.start_cast()
        # Populate the Recent Cast submenu from saved history.
        self.refresh_recent_menu()
        logger.debug("MiniCast APP started")

    def build_app_menu(self):
        self.toggle_menuitem = MenuItem(_("Stop Cast"), self.on_toggle_service_click, key="p")
        self.quit_menuitem = MenuItem(_("Quit"), self.quit, key="q")
        # Recent Cast block — always present (after status block), its children
        # are rebuilt whenever history changes / the menu is refreshed.
        self.recent_menuitem = MenuItem(_("Recent Cast"), children=[])
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
        self.rename_menuitem = MenuItem(_("Rename Device"), self.on_rename_device_click)

        player_settings = self.service.renderer.renderer_setting.build_menu()

        # Assemble the inline settings block. Each group is wrapped by a
        # separator so the top-level menu reads as distinct sections.
        status_block = [self.version_menuitem, self.ip_menuitem, None]
        # Recent Cast lives right under the status block so it is easy to reach
        # whether or not something is currently casting.
        recent_block = [self.recent_menuitem, None]
        player_block = player_settings + ([None] if len(player_settings) > 0 else [])
        preference_block = [self.menubar_icon_menuitem, self.rename_menuitem,
                            self.open_config_menuitem] + \
            ([None] if platform_options else []) + platform_options

        return status_block + recent_block + player_block + preference_block

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
        # Hide the progress line as well.
        if self.progress_menuitem:
            self.remove_menu_item_by_id(self.progress_menuitem.id)
        self.progress_menuitem = None

    def renderer_start(self):
        pass

    def renderer_av_uri(self, uri):
        logger.info("renderer_av_uri: " + uri)
        # Record into history (title from current DLNA state, fallback to uri).
        try:
            title = self.service.protocol.get_state_title() or uri
        except Exception:
            title = uri
        Setting.add_recent(uri, title)
        self.refresh_recent_menu()

        if self.copy_menuitem is not None:
            self.copy_menuitem.callback = lambda _: pyperclip.copy(uri)
        else:
            self.copy_menuitem = MenuItem(
                _("Copy Video URI"),
                key="c",
                callback=lambda _: pyperclip.copy(uri))
            self.append_menu_item_after(self.toggle_menuitem.id, self.copy_menuitem)

    def on_mpv_progress(self, title, position, duration, playing):
        """Update (or hide) the read-only progress line while casting."""
        if not playing:
            # Playback stopped — drop the line if present.
            if self.progress_menuitem is not None:
                self.remove_menu_item_by_id(self.progress_menuitem.id)
                self.progress_menuitem = None
            return
        display_title = self._truncate(title or _("Playing"), 40)
        text = "{} {} · {} / {}".format(
            _("PlayingMarker"), display_title, position, duration)
        if self.progress_menuitem is None:
            # Insert right after the "Copy Video URI" item, or after the
            # toggle item as a fallback.
            anchor_id = self.copy_menuitem.id if self.copy_menuitem \
                else self.toggle_menuitem.id
            self.progress_menuitem = MenuItem(text, enabled=False)
            self.append_menu_item_after(anchor_id, self.progress_menuitem)
        else:
            self.progress_menuitem.text = text
            self.update_menu()

    @staticmethod
    def _truncate(text, limit):
        text = str(text).replace('\n', ' ').strip()
        if len(text) <= limit:
            return text
        return text[:limit - 1] + '…'

    def refresh_recent_menu(self):
        """Rebuild the Recent Cast submenu children from saved history."""
        if self.recent_menuitem is None:
            return
        children = []
        history = Setting.get_recent(limit=8)
        if not history:
            children.append(MenuItem(_("No recent casts"), enabled=False))
        else:
            for entry in history:
                uri = entry.get('uri', '')
                title = self._truncate(entry.get('title') or uri, 40)
                # Each history entry is itself a submenu: [Replay] [Copy Link]
                entry_item = MenuItem(
                    title,
                    children=[
                        MenuItem(
                            _("Replay"),
                            callback=self._make_replay_callback(uri, title)),
                        MenuItem(
                            _("Copy Link"),
                            callback=self._make_copy_callback(uri)),
                    ])
                children.append(entry_item)
        self.recent_menuitem.children = children
        if self.platform is Platform.Darwin:
            # rumps builds its menu tree once at startup and does not observe
            # children list mutations, so the whole menu must be rebuilt to
            # reflect the new Recent Cast submenu.
            self.set_menu(self.menu)
        else:
            # pystray rebuilds the menu from self.menu on every open via a
            # lambda, so flagging it dirty is enough.
            self.update_menu()

    def _make_replay_callback(self, uri, title):
        def _replay(_):
            try:
                renderer = self.service.renderer
                protocol = self.service.protocol
                renderer.set_media_url(uri)
                renderer.set_media_title(title)
                protocol.set_state_url(uri)
                protocol.set_state('CurrentTrackTitle', title)
                protocol.set_state('CurrentTrackURI', uri)
                renderer.set_media_resume()
            except Exception as e:
                logger.error("replay failed: %s", e)
                self.notification(_("Error"), _("Cannot replay this item"))
        return _replay

    def _make_copy_callback(self, uri):
        def _copy(_):
            pyperclip.copy(uri)
        return _copy

    # --- menu click callbacks ---

    def on_open_config_click(self, item):
        self.open_directory(SETTING_DIR)

    def on_rename_device_click(self, item):
        """Pop a dialog and rename the DLNA device live."""
        current = Setting.get_friendly_name()
        name = self.prompt_text(
            _("Rename Device"), _("Enter a new device name:"), default=current)
        if not name or not name.strip():
            return
        name = name.strip()
        if name == current:
            return
        # Persist + apply to the running description / SSDP announcement.
        Setting.set(SettingProperty.DLNA_FriendlyName, name)
        Setting.set_temp_friendly_name(name)
        try:
            self.service.protocol.handler.build_description()
        except Exception as e:
            logger.error("rebuild description failed: %s", e)
        cherrypy.engine.publish('ssdp_update_ip')
        self.notification(_("MiniCast"), _("Device name updated"))

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
