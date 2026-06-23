"""
MiniCast setup script.
"""

import os
import sys
from setuptools import setup, find_packages
from setuptools import Command

from build_i18n import compile_po_to_mo

VERSION = "0.0.0"
with open('minicast/.version', 'r') as f:
    VERSION = f.read().strip()
LONG_DESCRIPTION = ""
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        LONG_DESCRIPTION = f.read()

# Core deps (no requests: update checker removed in MiniCast).
INSTALL = ["appdirs", "cherrypy", "lxml", "psutil", "portend"]
PACKAGES = find_packages()

if sys.platform == 'darwin':
    INSTALL += ["rumps", "pyperclip"]
elif sys.platform == 'win32':
    INSTALL += ["pillow", "pyperclip", "pystray", "pywin32"]
else:
    INSTALL += ["pillow", "pystray", "pyperclip"]

PO_DIR = os.path.join('i18n', 'zh_CN', 'LC_MESSAGES')
PO_FILE = os.path.join(PO_DIR, 'minicast.po')
MO_FILE = os.path.join(PO_DIR, 'minicast.mo')


class CompileCatalog(Command):
    """Compile ``i18n/zh_CN/LC_MESSAGES/minicast.po`` into ``minicast.mo``.

    Usage::

        python setup.py compile_catalog

    Run this whenever the ``.po`` source is edited, otherwise the runtime will
    keep serving the stale compiled catalog. Equivalent to running
    ``python build_i18n.py`` directly.
    """

    description = "compile gettext .po catalogs to binary .mo"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.exists(PO_FILE):
            raise SystemExit("catalog source not found: %s" % PO_FILE)
        compile_po_to_mo(PO_FILE, MO_FILE)
        print("compiled %s -> %s" % (PO_FILE, MO_FILE))


setup(
    name="minicast",
    version=VERSION,
    author="MiniCast",
    description="a lightweight DLNA media renderer (mpv based)",
    license="GPL3",
    url="https://github.com/",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    classifiers=["Topic :: Multimedia :: Sound/Audio",
                 "Topic :: Multimedia :: Video",
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10',
                 'Programming Language :: Python :: 3.11',
                 'Programming Language :: Python :: 3.12',
                 'Operating System :: MacOS :: MacOS X',
                 'Operating System :: Microsoft :: Windows :: Windows NT/2000',
                 'Operating System :: POSIX',
                 ],
    platforms=["MacOS X", "Windows", "POSIX"],
    keywords=["mpv", "dlna", "renderer", "cast"],
    install_requires=INSTALL,
    packages=PACKAGES,
    include_package_data=True,
    cmdclass={'compile_catalog': CompileCatalog},
    entry_points={
        'console_scripts': [
            'minicast = minicast.app:gui',
            'minicast-cli = minicast.app:cli',
        ]
    },
    python_requires=">=3.9",
)
