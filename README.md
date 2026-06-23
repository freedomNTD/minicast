# MiniCast

A lightweight, cross-platform DLNA / UPnP media renderer that turns your PC into a cast target. Built on [mpv](https://mpv.io) for playback and runs as a system-tray app on Windows, macOS, and Linux.

> 一个轻量级、跨平台的 DLNA / UPnP 媒体渲染器，能把你的电脑变成投屏接收端。基于 [mpv](https://mpv.io) 播放，以系统托盘程序形式运行于 Windows、macOS 和 Linux。

---

## ✨ Features | 功能特性

- **Cast receiver** — any DLNA control point (VLC, BubbleUPnP, Windows "Cast to Device", etc.) can discover and play to MiniCast.
- **mpv-powered playback** — full format support, hardware decoding, configurable window position & size.
- **Tray-native UI** — lives in the system tray; no main window, no clutter. Flat, separator-grouped menu.
- **Cross-platform** — Windows / macOS / Linux.
- **i18n** — English & 简体中文, switches with the system language.

> - **投屏接收** — 任何 DLNA 控制端（VLC、BubbleUPnP、Windows「投放到设备」等）都能发现并向 MiniCast 投屏。
> - **基于 mpv** — 全格式支持、硬件解码、窗口位置与大小可配置。
> - **原生托盘界面** — 仅驻留系统托盘，无主窗口、无干扰；采用扁平的、分隔符分组的菜单结构。
> - **跨平台** — Windows / macOS / Linux。
> - **国际化** — 中英双语，随系统语言自动切换。

---

## 📷 Tray menu | 托盘菜单

The tray menu is laid out as a single, separator-grouped list (no nested "Settings ▸" submenu):

> 托盘菜单采用扁平结构，用分隔符分区（没有嵌套的「Setting ▸」子菜单）：

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

| English | 中文 |
|---|---|
| Stop Cast / Start Cast | 停止投屏 / 开始投屏 |
| Copy Video URI | 复制视频链接 |
| Listening | 监听 |
| Player Position | 播放器位置 |
| Player Size | 播放器大小 |
| Hardware Decode | 硬件解码 |
| Player Ontop | 窗口置顶 |
| Appearance | 外观 |
| Open Config Directory | 打开配置目录 |
| Start At Login | 开机自启 |
| Quit | 退出 |

---

## 🚀 Quick start | 快速开始

### Windows (packaged exe)

Download `MiniCast.exe` from [Releases](../../releases), double-click to run. It appears in the system tray.

> 从 [Releases](../../releases) 下载 `MiniCast.exe`，双击运行。程序会出现在系统托盘。

### Run from source | 从源码运行

**Requirements | 环境要求：** Python 3.9+

```bash
# 1. install dependencies | 安装依赖
pip install -r requirements/common.txt
# Windows:  pip install pystray pillow pyperclip pywin32
# macOS:    pip install rumps pyperclip
# Linux:    pip install pystray pillow pyperclip

# 2. fetch the mpv player binary | 准备 mpv 播放器
#    put mpv.exe (Windows) / mpv (macOS,Linux) into ./bin/

# 3. run | 运行
python minicast.py
```

---

## 🔧 Configuration | 配置

Config & log location | 配置与日志位置:

- **Windows**: `%APPDATA%\MiniCast\`
- **macOS**: `~/Library/Application Support/MiniCast/`
- **Linux**: `~/.config/minicast/`

`minicast_setting.json` stores your preferences; `minicast.log` is the runtime log.

> `minicast_setting.json` 存储你的偏好设置；`minicast.log` 是运行时日志。

### Translations | 翻译

Source strings live in `i18n/zh_CN/LC_MESSAGES/minicast.po`; the runtime only reads the compiled `minicast.mo`. After editing the `.po`, recompile it (no external `msgfmt` needed):

> 翻译源文件在 `i18n/zh_CN/LC_MESSAGES/minicast.po`，运行时只读取编译后的 `minicast.mo`。修改 `.po` 后需重新编译（无需安装外部 `msgfmt`）：

```bash
python build_i18n.py            # or: python setup.py compile_catalog
```

## How it works | 工作原理

MiniCast is a self-contained UPnP/DLNA stack:

- **SSDP** (`ssdp.py`) — device discovery on the local network (multicast M-SEARCH / NOTIFY).
- **Device description** (`xml/`) — serves `Description.xml` and the service SCPDs.
- **HTTP server** (`server.py`, CherryPy) — implements `AVTransport` and `RenderingControl` services.
- **Renderer** (`renderer.py`, `minicast_renderer/mpv.py`) — bridges UPnP SetAVTransportURI / Play / Pause / Stop to an mpv player instance.

> MiniCast 是一个自包含的 UPnP/DLNA 协议栈：
>
> - **SSDP**（`ssdp.py`）— 局域网设备发现（组播 M-SEARCH / NOTIFY）。
> - **设备描述**（`xml/`）— 提供 `Description.xml` 和各服务的 SCPD 描述。
> - **HTTP 服务**（`server.py`，基于 CherryPy）— 实现 `AVTransport` 和 `RenderingControl` 服务。
> - **渲染器**（`renderer.py`、`minicast_renderer/mpv.py`）— 把 UPnP 的 SetAVTransportURI / Play / Pause / Stop 桥接到 mpv 播放器实例。

## 🏗️ Build | 打包

Package a single-file `MiniCast.exe` (Windows) using PyInstaller:

> 用 PyInstaller 打包成单文件 `MiniCast.exe`（Windows）：

```bash
pip install pyinstaller pywin32
pyinstaller MiniCast.spec --noconfirm
# output | 产物: dist/MiniCast.exe
```

Other build tools | 其他构建工具：

| Script | Purpose |
|---|---|
| `build_i18n.py` | Compile `.po` → `.mo` translations (pure Python, no `msgfmt` needed) |
| `make_icons.py` | Regenerate app/tray icons from scratch via Pillow (Cast glyph, blue→violet gradient) |
| `setup.py compile_catalog` | Same as `build_i18n.py`, exposed as a setuptools command |

> | 脚本 | 用途 |
> |---|---|
> | `build_i18n.py` | 编译 `.po` → `.mo` 翻译（纯 Python，无需 `msgfmt`） |
> | `make_icons.py` | 用 Pillow 从零重新生成应用/托盘图标（Cast 符号，蓝紫渐变） |
> | `setup.py compile_catalog` | 等同于 `build_i18n.py`，作为 setuptools 命令暴露 |

## 📄 License | 许可证

[GPL-3.0](LICENSE)

---

## 🤝 Credits | 致谢

MiniCast is inspired by [Macast](https://github.com/xfangfang/Macast). Built on [mpv](https://mpv.io), [CherryPy](https://cherrypy.dev/), [pystray](https://github.com/moses-palmer/pystray), and [rumps](https://github.com/jaredks/rumps).

> MiniCast 受 [Macast](https://github.com/xfangfang/Macast) 启发。基于 [mpv](https://mpv.io)、[CherryPy](https://cherrypy.dev/)、[pystray](https://github.com/moses-palmer/pystray)、[rumps](https://github.com/jaredks/rumps) 构建。
