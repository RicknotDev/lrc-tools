# lrc-tools

```/dev/null/logo.txt#L1-5
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\__,_|\___|\__|
```

Terminal synced lyrics toolkit for Linux with CLI utilities, MPRIS/playerctl integration, and a Textual TUI.

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-informational)](#)
[![Release](https://img.shields.io/github/v/release/RicknotDev/lrc-tools)](https://github.com/RicknotDev/lrc-tools/releases)

> Quick install: `python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"`
>
> Local dev install: `make install`

## Features

| Tool | What it does | Example command |
|---|---|---|
| `lrc-tools` / `lt` | Launches the interactive terminal UI | `lrc-tools` |
| `lrc-fetch` | Scans your music library and downloads synced lyrics | `lrc-fetch --audio-dir ~/Music --output-dir ~/.local/share/lrc-tools/lyrics/raw` |
| `lrc-processor` | Splits long phrases and generates word-level `.wlrc` files | `lrc-processor --lrc-dir raw --audio-dir ~/Music --output-dir processed --wlrc` |
| `lrc-vis` | Displays synced lyrics in the terminal while your player runs | `lrc-vis --lrc-dir ~/.local/share/lrc-tools/lyrics/processed --wlrc` |

## Installation

### From GitHub

- Editable local install with all runtime dependencies: `bash setup.sh`
- Editable local install via Makefile: `make install`
- Minimal editable install: `make install-minimal`
- Direct pip install with the default full dependency set: `python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"`

### System requirements

- Python 3.12+
- Linux
- `playerctl`
- `ffmpeg` / `ffprobe`
- `PyYAML`

Default Python install includes:

- `textual` for the TUI
- `mutagen` for audio metadata
- `syncedlyrics` for fallback lyric search
- `librosa` for better word timing

Handy development commands:

- `make install`
- `make uninstall`
- `make test`
- `make build`
- `make clean`

## Quick start

1. Install the package.
2. Make sure `~/.local/bin` is in your `PATH`.
3. Run `lrc-tools` or `lt`.
4. Download `.lrc` files with `lrc-fetch`.
5. Convert them to `.wlrc` with `lrc-processor --wlrc`.
6. Start the visualizer with `lrc-vis --wlrc`.

## Documentation

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/file-formats.md`](docs/file-formats.md)
- [`docs/troubleshooting.md`](docs/troubleshooting.md)

## GitHub visibility suggestions

### Topics

`lyrics`, `lrc`, `terminal`, `tui`, `mpris`, `playerctl`, `music`, `python`, `cli`, `syncedlyrics`, `lrclib`, `linux`, `terminal-ui`, `ascii-art`, `karaoke`, `lyrics-viewer`, `music-tools`

### Repository description

Terminal synced lyrics viewer for Linux with MPRIS/playerctl support, LRCLIB fetching, and a Textual TUI.

### Social preview idea

Use an OG image showing a dark Linux terminal with the ASCII logo, a large lyric line in progress, a progress bar, and small labels for `MPRIS`, `playerctl`, and `.wlrc`.

<details>
<summary>🇪🇸 Leer en español</summary>

## Descripción

`lrc-tools` es una suite para letras sincronizadas en la terminal de Linux, con utilidades CLI, integración con MPRIS/`playerctl` y una interfaz TUI con Textual.

## Instalación rápida

- Instalación desde GitHub con todas las dependencias por defecto: `python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"`
- Instalación editable local: `bash setup.sh`
- Instalación editable con Makefile: `make install`
- Instalación mínima: `make install-minimal`

## Herramientas

| Herramienta | Qué hace | Ejemplo |
|---|---|---|
| `lrc-tools` / `lt` | Abre la interfaz interactiva | `lrc-tools` |
| `lrc-fetch` | Escanea tu música y descarga letras sincronizadas | `lrc-fetch --audio-dir ~/Music --output-dir ~/.local/share/lrc-tools/lyrics/raw` |
| `lrc-processor` | Procesa `.lrc` y genera `.wlrc` palabra por palabra | `lrc-processor --lrc-dir raw --audio-dir ~/Music --output-dir processed --wlrc` |
| `lrc-vis` | Muestra las letras sincronizadas en la terminal | `lrc-vis --lrc-dir ~/.local/share/lrc-tools/lyrics/processed --wlrc` |

## Inicio rápido

1. Instalá el paquete.
2. Verificá que `~/.local/bin` esté en el `PATH`.
3. Ejecutá `lrc-tools` o `lt`.
4. Descargá letras con `lrc-fetch`.
5. Procesalas con `lrc-processor --wlrc`.
6. Abrí el visualizador con `lrc-vis --wlrc`.

## Dependencias instaladas por defecto

- `textual` para la TUI
- `mutagen` para metadata de audio
- `syncedlyrics` como fallback de búsqueda
- `librosa` para timing más preciso por palabra

## Comandos útiles

- `make install`
- `make uninstall`
- `make test`
- `make build`
- `make clean`

## Documentación

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/file-formats.md`](docs/file-formats.md)
- [`docs/troubleshooting.md`](docs/troubleshooting.md)

</details>
