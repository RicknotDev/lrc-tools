# lrc-tools

```/dev/null/logo.txt#L1-5
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\__,_|\___|\__|
```

A Linux terminal app for fetching, processing, and displaying synced lyrics with a polished Textual TUI.

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-informational)](#)
[![Release](https://img.shields.io/github/v/release/RicknotDev/lrc-tools)](https://github.com/RicknotDev/lrc-tools/releases)

## What is this?

`lrc-tools` helps you do three things from the terminal:

1. **Fetch** synced lyrics for the songs in your library.
2. **Process** those lyrics into a word-level format for smoother playback.
3. **Visualize** the lyrics in real time while music is playing.

If you are new, the easiest path is:

- install the app
- open `lrc-tools`
- choose your music folder
- run fetch
- run process
- launch the visualizer

## Main commands

| Command | What it does | Typical use |
|---|---|---|
| `lrc-tools` / `lt` | Opens the interactive TUI | Best starting point for most users |
| `lrc-fetch` | Downloads `.lrc` lyrics | Build your lyrics library |
| `lrc-processor` | Converts `.lrc` into `.wlrc` | Better word-by-word playback |
| `lrc-vis` | Shows synced lyrics in the terminal | Manual visualizer launch |

## Installation

### Option A — easiest local install

From a clone of the repo:

- `make install`

This installs the app in editable mode with the default dependency set.

### Option B — convenience script

- `bash setup.sh`

This does the same install in a simple wrapper.

### Option C — install directly from GitHub

- `python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"`

## Requirements

You need:

- Linux
- Python 3.12+
- `playerctl`
- `ffmpeg` / `ffprobe`

The Python install already includes these runtime packages by default:

- `PyYAML`
- `textual`
- `mutagen`
- `syncedlyrics`
- `librosa`

### Arch Linux example

```/dev/null/install-arch.sh#L1-2
sudo pacman -S playerctl ffmpeg
python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"
```

## First-time setup

### 1. Make sure your binaries are in `PATH`

```/dev/null/path.sh#L1-1
export PATH="$HOME/.local/bin:$PATH"
```

### 2. Open the TUI

```/dev/null/open-tui.sh#L1-1
lrc-tools
```

### 3. In the interface

Follow this order:

1. **Configure paths**
2. **Fetch lyrics**
3. **Process lyrics**
4. **Launch visualizer**

## Typical workflow

### Interactive workflow

```/dev/null/workflow-tui.sh#L1-1
lrc-tools
```

Inside the TUI:

- choose your music folder
- fetch lyrics into the raw lyrics directory
- process them into `.wlrc`
- select a song and launch the visualizer

### CLI workflow

```/dev/null/workflow-cli.sh#L1-9
RAW=~/.local/share/lrc-tools/lyrics/raw
OUT=~/.local/share/lrc-tools/lyrics/processed

lrc-fetch --audio-dir ~/Music --output-dir "$RAW"
lrc-processor \
  --lrc-dir "$RAW" \
  --audio-dir ~/Music \
  --output-dir "$OUT" \
  --wlrc
lrc-vis --lrc-dir "$OUT" --wlrc
```

## Where files are stored

By default, `lrc-tools` uses XDG-style paths:

- raw lyrics: `~/.local/share/lrc-tools/lyrics/raw`
- processed lyrics: `~/.local/share/lrc-tools/lyrics/processed`
- config: `~/.config/lrc-tools/config.yaml`

## Helpful developer commands

- `make install`
- `make install-minimal`
- `make reinstall`
- `make uninstall`
- `make test`
- `make build`
- `make clean`

## Troubleshooting

### `command not found`

Your shell probably does not include `~/.local/bin` yet.

### TUI does not open

Install the full dependency set again:

```/dev/null/reinstall.sh#L1-1
make reinstall
```

### Visualizer does not find the current song

Check:

- `playerctl status`
- the lyrics exist in the processed directory
- your filenames and tags are consistent

### Want the full docs?

See:

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/file-formats.md`](docs/file-formats.md)
- [`docs/troubleshooting.md`](docs/troubleshooting.md)

<details>
<summary>🇪🇸 Leer en español</summary>

## Qué es esto

`lrc-tools` es una app de terminal para Linux que permite descargar, procesar y mostrar letras sincronizadas con una TUI más amigable para usuarios nuevos.

## Instalación

### Opción A — instalación local recomendada

- `make install`

### Opción B — wrapper simple

- `bash setup.sh`

### Opción C — instalación desde GitHub

- `python3 -m pip install --user "git+https://github.com/RicknotDev/lrc-tools#egg=lrc-tools[full,timing]"`

## Requisitos

- Linux
- Python 3.12+
- `playerctl`
- `ffmpeg` / `ffprobe`

## Primer uso

1. Ejecutá `lrc-tools`
2. Configurá la carpeta de música
3. Descargá letras con **Fetch lyrics**
4. Procesalas con **Process lyrics**
5. Abrí el visualizador con **Launch visualizer**

## Flujo típico por CLI

```/dev/null/workflow-cli-es.sh#L1-9
RAW=~/.local/share/lrc-tools/lyrics/raw
OUT=~/.local/share/lrc-tools/lyrics/processed

lrc-fetch --audio-dir ~/Music --output-dir "$RAW"
lrc-processor \
  --lrc-dir "$RAW" \
  --audio-dir ~/Music \
  --output-dir "$OUT" \
  --wlrc
lrc-vis --lrc-dir "$OUT" --wlrc
```

## Rutas por defecto

- letras crudas: `~/.local/share/lrc-tools/lyrics/raw`
- letras procesadas: `~/.local/share/lrc-tools/lyrics/processed`
- config: `~/.config/lrc-tools/config.yaml`

## Comandos útiles

- `make install`
- `make reinstall`
- `make uninstall`
- `make test`
- `make build`
- `make clean`

## Documentación

- [`docs/configuration.md`](docs/configuration.md)
- [`docs/file-formats.md`](docs/file-formats.md)
- [`docs/troubleshooting.md`](docs/troubleshooting.md)

</details>
