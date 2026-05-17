
# lrc-tools

**Letras sincronizadas en la terminal** — descarga, procesa y visualiza lyrics en ASCII grande, al ritmo de tu reproductor (MPRIS / `playerctl`).

Interfaz TUI interactiva (`lrc-tools` / `lt`) + herramientas CLI para quien prefiera scripts.

```
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\__,_|\___|\__|
```

---

## Repositorio


| | |
|---|---|
| **Código fuente** | [**https://github.com/RicknotDev/lrc-tools**](https://github.com/RicknotDev/lrc-tools) |
| **Clonar** | `git clone https://github.com/RicknotDev/lrc-tools` |
| **Guía completa** | [docs/README.md](docs/README.md) |
| **Licencia** | [MIT](LICENSE) |

```bash
git clone https://github.com/RicknotDev/lrc-tools
cd lrc-tools
bash setup.sh
```

## Inicio rápido

```bash
bash setup.sh
export PATH="$HOME/.local/bin:$PATH"

lrc-tools    # TUI interactiva (alias: lt)
```

- Menú: setup, fetch, process, **elegir canción** + visualizer, rutas, dependencias.
- Atajos: `f` fetch · `p` process · `v` visualizer · `r` rápido · `q` salir.
- Letras (XDG): `~/.local/share/lrc-tools/lyrics/{raw,processed}`

### CLI manual

```bash
MUSIC=~/Music
RAW=~/.local/share/lrc-tools/lyrics/raw
OUT=~/.local/share/lrc-tools/lyrics/processed

lrc-fetch --audio-dir "$MUSIC" --output-dir "$RAW"
lrc-processor --lrc-dir "$RAW" --audio-dir "$MUSIC" --output-dir "$OUT" --wlrc
lrc-vis --lrc-dir "$OUT" --wlrc
```

Uso diario: `lt` → **Launch visualizer** → elegí canción (reproduce audio + letra) o **Automático** (solo playerctl).

Reproducción local al elegir tema: **mpv** o **ffplay** (`sudo pacman -S mpv ffmpeg`).

---

## Desinstalar

```bash
bash uninstall.sh           # interactivo
bash uninstall.sh -y        # borra bins, paquete, config y letras
```

---

## Dependencias

**Requeridas:** Python ≥ 3.12, `python-pyyaml`, `ffmpeg` (ffprobe), `playerctl`

**Recomendadas:** `python-mutagen`, `python-syncedlyrics`, `textual` (TUI)

**Opcional:** `python-librosa` — timing por palabra más fino

En Arch: `sudo pacman -S playerctl ffmpeg python-pyyaml python-mutagen`

---

## Cómo funciona

| Herramienta | Función |
|-------------|---------|
| `lrc-fetch` | Escanea tu música y descarga `.lrc` desde [LRCLIB](https://lrclib.net) (+ syncedlyrics) |
| `lrc-processor` | Convierte frases largas a `.wlrc` (palabra por palabra) |
| `lrc-vis` | Muestra la letra en bloques ASCII según `playerctl` |
| `lrc-tools` / `lt` | TUI: todo lo anterior sin memorizar flags |

Los nombres de archivo de letra deben coincidir con el audio (`Artista - Título.mp3` → mismo stem `.lrc` / `.wlrc`).

---

## Configuración

`~/.config/lrc-tools/config.yaml` — plantilla: `config_example.yaml`

```yaml
puller:
  preserve_structure: true   # refleja subcarpetas de tu música

visualizer:
  default_font: block
  refresh_rate: 0.05
```

---

## Tests

```bash
./scripts/run_tests.sh
```

---

## Notas

- La precisión del timing mejora en temas con letra hablada rápida; temas muy under a veces no están en LRCLIB.
- Proyecto en evolución; para problemas concretos revisá [docs/README.md](docs/README.md) o abrí un issue en **tu repositorio** (enlace arriba).

---

## Créditos

Fork y mejora de un proyecto de visualización de letras en terminal; empaquetado como **tacos-terminal-lyrics** con TUI, rutas XDG y asistente de setup.
