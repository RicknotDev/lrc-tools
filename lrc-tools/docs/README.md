# lrc-tools — Guía completa

Documentación de **lrc-tools**: letras sincronizadas en la terminal, con interfaz TUI y herramientas CLI.

**Repositorio:** configurá la URL en el [README principal](../README.md#repositorio) (`YOUR_USERNAME/lrc-tools`).

---

## Índice

1. [¿Qué hace este proyecto?](#qué-hace-este-proyecto)
2. [Arquitectura](#arquitectura)
3. [Rutas y archivos (XDG)](#rutas-y-archivos-xdg)
4. [Instalación](#instalación)
5. [Uso diario: la TUI](#uso-diario-la-tui)
6. [Herramientas CLI](#herramientas-cli)
7. [Flujo de datos](#flujo-de-datos)
8. [Configuración](#configuración)
9. [Dependencias](#dependencias)
10. [Desarrollo y tests](#desarrollo-y-tests)
11. [Solución de problemas](#solución-de-problemas)

---

## ¿Qué hace este proyecto?

1. **Descarga** letras sincronizadas (`.lrc`) para tu biblioteca de música.
2. **Procesa** esas letras a formato **palabra por palabra** (`.wlrc`) para el visualizador.
3. **Muestra** la letra actual en **ASCII grande** en la terminal, sincronizada con lo que suena en tu reproductor (Spotify, VLC, etc.) vía **MPRIS** / `playerctl`.

No necesitás recordar comandos largos: abrís **`lrc-tools`** (o **`lt`**) y todo se hace desde el menú.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  lrc-tools / lt          TUI (Textual) — punto de entrada   │
│  lrc-tools-auto          Redirige a lrc-tools               │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    ┌─────────┐      ┌─────────────┐    ┌──────────┐
    │  core   │      │  tui/app    │    │ setup.sh │
    │  rutas  │      │  pantallas  │    │ instala  │
    │  estado │      │  menú/logs  │    │ bins     │
    └────┬────┘      └─────────────┘    └──────────┘
         │ subprocess
         ▼
┌────────────────────────────────────────────────────────────┐
│  lrc-fetch      → puller.py + LRCLIB + syncedlyrics          │
│  lrc-processor  → processor_main.py → .wlrc                  │
│  lrc-vis        → visualizer_* + playerctl                   │
└────────────────────────────────────────────────────────────┘
```

| Módulo | Rol |
|--------|-----|
| `core.py` | Rutas XDG, estado del usuario, comprobación de deps, construcción de comandos |
| `tui/app.py` | Aplicación Textual: menú, logs en vivo, wizard |
| `tui/dir_browser.py` | Selector visual de carpeta de música |
| `puller.py` | Búsqueda y descarga de LRC |
| `processor_main.py` | División de frases y timing por palabra |
| `visualizer_main.py` | Bucle de visualización + `playerctl` |
| `config.py` | Carga de `config.yaml` |

Tras `setup.sh`, el paquete Python vive en `~/.config/lrc-tools/lrc_tools/` y los ejecutables en `~/.local/bin/`.

---

## Rutas y archivos (XDG)

| Qué | Ruta por defecto |
|-----|------------------|
| Configuración | `~/.config/lrc-tools/config.yaml` |
| Estado (carpeta música, etc.) | `~/.config/lrc-tools/.setup_done` |
| LRC descargados | `~/.local/share/lrc-tools/lyrics/raw` |
| WLRC procesados | `~/.local/share/lrc-tools/lyrics/processed` |
| Paquete instalado | `~/.config/lrc-tools/lrc_tools/` |
| Fuentes custom | `~/.config/lrc-tools/custom_fonts.json` |

Se respetan `XDG_CONFIG_HOME` y `XDG_DATA_HOME` si están definidas.

`preserve_structure: true` en config hace que las letras repliquen la estructura de subcarpetas de tu música (p. ej. `raw/Artist/Album/song.lrc`).

---

## Instalación

```bash
git clone https://github.com/YOUR_USERNAME/lrc-tools.git
cd lrc-tools
bash setup.sh
```

(Reemplazá `YOUR_USERNAME` por tu usuario de GitHub; ver también la sección **Repositorio** del README principal.)

### Desinstalar

```bash
bash uninstall.sh              # interactivo (pregunta por config y letras)
bash uninstall.sh --keep-data    # solo bins + paquete Python
bash uninstall.sh -y             # borra todo sin preguntar
```

No elimina paquetes `pacman` ni librerías pip instaladas para otras apps.

`setup.sh` instala dependencias Python (yaml, mutagen, syncedlyrics, **textual**), copia el paquete, crea directorios XDG y enlaza:

- `lrc-fetch`, `lrc-processor`, `lrc-vis`
- `lrc-tools`, `lt` (alias)

Asegurate de tener `~/.local/bin` en el `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Sistema (Arch):

```bash
sudo pacman -S playerctl ffmpeg python-pyyaml python-mutagen
pip install syncedlyrics textual --break-system-packages
```

---

## Uso diario: la TUI

```bash
lrc-tools    # o: lt
```

### Menú principal

| Tecla | Acción |
|-------|--------|
| `1` | Asistente de setup (primera vez) |
| `2` / `f` | Descargar letras (fetch) |
| `3` / `p` | Procesar `.lrc` → `.wlrc` |
| `4` / `v` | Elegir canción y abrir visualizador |
| `5` | Configurar carpeta de música |
| `6` | Comprobar / instalar dependencias |
| `7` | Ver configuración |
| `r` | Modo rápido: fetch + process |
| `l` | Mostrar u ocultar panel de logs |
| `R` | Actualizar panel de estado |
| `q` | Salir |

El **panel derecho** muestra: ruta de música, cantidad de canciones, `.lrc`, `.wlrc`, estado de herramientas y deps.

### Primera vez

1. Abrí `lrc-tools`.
2. Tecla **`6`** — instalá lo que falte (playerctl, ffmpeg, textual…).
3. Tecla **`1`** — wizard: instala bins, crea carpetas XDG, fetch y process.
4. Tecla **`5`** — si tu música no está en `~/Music`, elegí la carpeta con **Examinar**.
5. Tecla **`v`** — elegí **Automático** (sigue el reproductor) o una canción de la lista; reproducí el tema y mirá la terminal.

### Modo rápido (avanzado)

```bash
lrc-tools --quick
# o: lt -r
```

Ejecuta fetch y process seguidos, sin pasar por el menú.

---

## Herramientas CLI

Siguen existiendo para scripts o automatización:

```bash
MUSIC=~/Music
RAW=~/.local/share/lrc-tools/lyrics/raw
OUT=~/.local/share/lrc-tools/lyrics/processed

lrc-fetch --audio-dir "$MUSIC" --output-dir "$RAW" --config ~/.config/lrc-tools/config.yaml
lrc-processor --lrc-dir "$RAW" --audio-dir "$MUSIC" --output-dir "$OUT" --wlrc
lrc-vis --lrc-dir "$OUT" --wlrc
lrc-vis --lrc-dir "$OUT" --wlrc --lrc-file "$OUT/Artist - Song.wlrc" --pin
```

La TUI construye estos mismos comandos internamente; no hace falta escribirlos a mano.

**Elegir canción:** en el menú **Launch visualizer** podés buscar por nombre, elegir un `.wlrc` fijo (`--pin`) o **Automático** para que coincida con lo que suena en el reproductor.

Al elegir una canción concreta, se reproduce el audio en segundo plano con **mpv** (preferido) o **ffplay**, sincronizado con la letra. Modo **Automático** sigue usando solo tu reproductor (playerctl), sin duplicar audio.

---

## Flujo de datos

```
  ~/Music/**/*.mp3
        │
        ▼  lrc-fetch (tags → LRCLIB / syncedlyrics)
  ~/.local/share/lrc-tools/lyrics/raw/**/*.lrc
        │
        ▼  lrc-processor (--wlrc, ffprobe, opcional librosa)
  ~/.local/share/lrc-tools/lyrics/processed/**/*.wlrc
        │
        ▼  lrc-vis + playerctl (posición de reproducción)
  Terminal: letra ASCII sincronizada
```

- **Matching**: el nombre del `.lrc` / `.wlrc` debe coincidir con el del audio (o ruta relativa si `preserve_structure` está activo).
- **MPRIS**: `playerctl` lee título/artista/posición del reproductor activo.

---

## Configuración

Archivo: `~/.config/lrc-tools/config.yaml`

Ejemplo generado por la TUI:

```yaml
processor:
  max_phrase_duration: 2.5
  max_words_per_phrase: 8
  use_onset_detection: false   # true si tenés librosa

puller:
  search_threads: 4
  download_threads: 4
  preserve_structure: true

visualizer:
  default_font: block
  refresh_rate: 0.05
```

Desde la TUI: menú **Settings** → regenerar o ver valores. Editar el YAML a mano también funciona; los CLI leen `--config`.

---

## Dependencias

| Componente | Uso |
|------------|-----|
| `playerctl` | Sincronizar con el reproductor |
| `ffmpeg` / `ffprobe` | Duración del audio al procesar |
| `python-pyyaml` | Leer config |
| `mutagen` | Tags ID3/Vorbis para mejor búsqueda |
| `syncedlyrics` | Fallback si LRCLIB no tiene la tema |
| `librosa` | (opcional) timing más fino por palabra |
| `textual` | Interfaz TUI |

---

## Desarrollo y tests

Desde el clon del repo (sin instalar):

```bash
export LRC_TOOLS_REPO="$PWD"
export PATH="$PWD:$HOME/.local/bin:$PATH"
./lrc-tools
```

Tests (solo stdlib + unittest; TUI se omite si no hay textual):

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

O:

```bash
python3 -m unittest discover -s tests -v
```

| Archivo | Qué prueba |
|---------|------------|
| `tests/test_core.py` | Estado, conteos, config, comandos, validación de rutas |
| `tests/test_tui.py` | Arranque de la app y diálogos (requiere textual) |

---

## Solución de problemas

| Síntoma | Qué revisar |
|---------|-------------|
| `lrc-tools: command not found` | `export PATH="$HOME/.local/bin:$PATH"` |
| No sincroniza con el player | `playerctl status`, reproductor con MPRIS |
| Fetch encuentra poco | Tags con mutagen; tema en LRCLIB; internet |
| Process no genera wlrc | `ffprobe` instalado; audio con mismo nombre/ruta que `.lrc` |
| Vis no muestra nada | ¿Hay `.wlrc` en processed? ¿Reproduciendo algo? |
| TUI no abre | `pip install textual --break-system-packages` |
| Setup.sh falla en wizard | `export LRC_TOOLS_REPO=/ruta/al/repo` antes de `lrc-tools` |

---

## Resumen de comandos

| Comando | Descripción |
|---------|-------------|
| `lrc-tools` / `lt` | Interfaz TUI principal |
| `lrc-tools --quick` | Fetch + process automático |
| `lrc-fetch` | Solo descarga |
| `lrc-processor` | Solo procesado |
| `lrc-vis` | Solo visualizador |
| `lrc-tools-auto` | Alias legacy → `lrc-tools` |

**Uso diario recomendado:** `lt` → **`v`** (Launch visualizer).
