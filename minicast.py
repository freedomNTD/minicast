# MiniCast - a lightweight DLNA media renderer.

import os
import sys
import gettext
import logging

from minicast import Setting
from minicast.app import gui
from minicast.utils import SETTING_DIR

logger = logging.getLogger("MiniCast")
logger.setLevel(logging.DEBUG)


def get_base_path(path="."):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()
    return os.path.join(base_path, path)


def set_mpv_default_path():
    mpv_path = 'mpv'
    if sys.platform == 'darwin':
        mpv_path = get_base_path('bin/MacOS/mpv')
    elif sys.platform == 'win32':
        mpv_path = get_base_path('bin/mpv.exe')
    Setting.mpv_default_path = mpv_path
    return mpv_path


def get_lang():
    locale = Setting.get_locale()
    i18n_path = get_base_path('i18n')
    if not os.path.exists(os.path.join(i18n_path, locale, 'LC_MESSAGES', 'minicast.mo')):
        locale = locale.split("_")[0]
    logger.info("MiniCast Loading Language: %s", locale)
    try:
        lang = gettext.translation('minicast', localedir=i18n_path, languages=[locale])
        lang.install()
    except Exception:
        import builtins
        builtins.__dict__['_'] = gettext.gettext
        logger.info("MiniCast Loading Default Language en_US")


def clear_env():
    log_path = os.path.join(SETTING_DIR, 'minicast.log')
    try:
        os.remove(log_path)
    except OSError:
        pass


if __name__ == '__main__':
    clear_env()
    get_lang()
    set_mpv_default_path()
    gui(lang=_)
