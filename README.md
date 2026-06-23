# MiniCast

A lightweight **DLNA Media Renderer** that turns your computer into a casting
target. Push videos, music or pictures from your phone (or any DLNA / UPnP
controller) and they play in **[mpv](https://mpv.io/)** on your desktop.

MiniCast runs as a small tray icon — no window, no clutter.

---

## Features

- 📺 **DLNA / UPnP renderer** — your computer shows up as a casting device on
  the same Wi-Fi / LAN. Cast from iOS, Android, Windows, anything that speaks DLNA.
- 🎬 **mpv powered playback** — hardware decoding, subtitle support, on-top window.
- 🖥️ **System tray UI** — start / stop casting, switch player position & size,
  toggle hardware decode, set start-at-login.
- 🔇 **Headless mode** — run without a tray (`--cli`) for servers / kiosks.
- 🌐 **i18n** — English + 简体中文 out of the box.
- 🪶 **Minimal** — no web UI, no plugin marketplace, no auto-updater phoning home.

## Requirements

- Python **3.9+**
- **mpv** player binary (`mpv` on PATH, or `bin/mpv.exe` / `bin/MacOS/mpv`)
- Platform tray lib: `pystray` (Windows/Linux) or `rumps` (macOS)

## Installation

```bash
# clone
git clone <your-repo-url> minicast
cd minicast

# install dependencies
pip install -r requirements/common.txt        # Windows / Linux
pip install -r requirements/darwin.txt        # macOS
pip install pywin32                            # Windows only (start-at-login)

# get mpv (Windows example)
mkdir bin
# place mpv.exe and vulkan-1.dll into bin/
```

## Usage

```bash
# tray UI (default)
python minicast.py

# headless / server mode
python -c "from minicast.app import cli; cli()"
```

Then open any DLNA controller on your phone (e.g.BubbleUPnP, VLC, Windows
"Cast to device"), pick **MiniCast** from the device list, and cast.

### Tray menu

The tray menu is laid out as a single, separator-grouped list (no nested
"Settings ▸" submenu):

```
Stop Cast                       ← toggle the renderer (Start Cast when idle)
Copy Video URI                  ← appears while casting
─────────────
MiniCast v1.2.0                 ← read-only status (grey)
Listening · 192.168.1.10:54321  ← read-only address (grey)
─────────────
Player Position ▸               ← corner / center placement
Player Size ▸                   ← small … fullscreen
Hardware Decode                 ← toggle
Player Ontop                    ← toggle
─────────────
Appearance ▸                    ← tray icon style
Open Config Directory
Start At Login                  ← packaged builds only
─────────────
Quit
```

## Configuration

Settings live in:
- Windows: `%LOCALAPPDATA%\MiniCast\`
- macOS:   `~/Library/Application Support/MiniCast/`
- Linux:   `~/.config/MiniCast/`

`minicast_setting.json` stores your preferences; `minicast.log` is the runtime log.

### Translations

Source strings live in `i18n/zh_CN/LC_MESSAGES/minicast.po`; the runtime only
reads the compiled `minicast.mo`. After editing the `.po`, recompile it (no
external `msgfmt` needed):

```bash
python build_i18n.py            # or: python setup.py compile_catalog
```

## How it works## How it works

```
┌─────────┐   SSDP discover    ┌──────────┐   IPC (pipe/socket)   ┌─────┐
│  Phone  │ ─────────────────▶ │ MiniCast │ ────────────────────▶ │ mpv │
│ (DLNA)  │ ◀─── SOAP action ─ │ (server) │ ◀─── player events ── │     │
└─────────┘                    └──────────┘                       └─────┘
```

MiniCast advertises itself via SSDP, answers DLNA SOAP requests (SetAVTransportURI,
Play, Pause, Seek, SetVolume …) over HTTP, and forwards them to mpv through its
JSON IPC interface. Player state flows back the same way to keep the controller
in sync.

## Project layout

```
minicast.py              entry point (tray UI)
minicast/
  app.py                 tray app + cast service wiring
  protocol.py            DLNA / UPnP protocol (SOAP, events)
  ssdp.py                SSDP device discovery
  server.py              HTTP service assembly
  plugin.py              cherrypy background-thread plugins
  renderer.py            renderer base class
  gui.py                 tray abstraction (pystray / rumps)
  utils.py               settings, IP detection, locale
  xml/                   DLNA service descriptors
  assets/                tray icons
minicast_renderer/
  mpv.py                 the mpv renderer (default player)
i18n/                    translations
```

## License

[MIT](LICENSE)
