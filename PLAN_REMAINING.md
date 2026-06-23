# lrc-tools — Plan de Fases Restantes

> Generado: 2026-06-22
> Completado: Fase 1 (Auditoría), Fase 2 (Estabilidad), Fase 3 (Instalación Universal)

---

## FASE 4 — EXPERIENCIA DE USUARIO

### CLI mejorado
- `lrc_tools/cli/fetch.py`, `process.py`, `vis.py`: agregar `rich` para colores
- Barra de progreso con `rich.progress.Progress` en fetch/process
- `--help` con ejemplos automáticos
- Validación de parámetros temprana (type checks antes de ejecutar)
- Manejo elegante de errores con `rich.traceback.install()`

### TUI mejorado
- `src/lrc_tools/tui/app.py`: partir en archivos separados por screen
- Mensajes de error con colores y sugerencias
- Tooltips en menú
- Confirmación antes de operaciones destructivas (ya existe parcialmente)
- Modo interactivo con pasos guiados (ya existe SetupWizard)

### Archivos a modificar
```
src/lrc_tools/cli/fetch.py     # rich progress, validación
src/lrc_tools/cli/process.py   # rich progress, validación
src/lrc_tools/cli/vis.py       # validación de --play/--audio-dir
src/lrc_tools/tui/app.py       # refactor a screens/ individuales
pyproject.toml                 # agregar rich como dep base
```

---

## FASE 5 — FUNCIONALIDADES NUEVAS

### Procesamiento LRC
- `src/lrc_tools/parser.py`: agregar `validate_lrc()` — validar timestamps, duplicados, formato
- `src/lrc_tools/parser.py`: agregar `repair_lrc()` — auto-fix timestamps inválidos
- `src/lrc_tools/parser.py`: agregar `offset_timestamps(delta)` — desplazar todos los timestamps
- `src/lrc_tools/parser.py`: agregar `merge_lrc(files)` — fusionar archivos LRC
- `src/lrc_tools/parser.py`: agregar `split_lrc(file, n)` — partir LRC en N partes

### Exportadores/Importadores
- `src/lrc_tools/exporters.py`: export a SRT (subtítulos)
- `src/lrc_tools/exporters.py`: export a ASS (Advanced SubStation Alpha)
- `src/lrc_tools/exporters.py`: export a JSON (portable)
- `src/lrc_tools/importers.py`: import desde SRT
- `src/lrc_tools/importers.py`: import desde JSON

### Lotes y Automatización
- `src/lrc_tools/cli/process.py`: flag `--watch` (modo vigilancia: reprocesa al detectar cambios)
- `src/lrc_tools/cli/fetch.py`: flag `--dry-run` (muestra qué se descargaría sin hacerlo)
- `src/lrc_tools/core.py`: backup automático antes de overwrite
- `src/lrc_tools/config.py`: perfiles de usuario (`--profile work`, `--profile home`)
- `src/lrc_tools/config.py`: presets (configuraciones predefinidas)

### Archivos nuevos
```
src/lrc_tools/exporters.py    # SRT, ASS, JSON export
src/lrc_tools/importers.py    # SRT, JSON import
```

---

## FASE 6 — ARQUITECTURA (Refactor Mayor)

### División del monolito TUI
Partir `src/lrc_tools/tui/app.py` (1127 líneas → archivos individuales):

```
src/lrc_tools/tui/
├── __init__.py
├── app.py                  # ~50 lines: LrcToolsApp, run_tui, main
├── screens/
│   ├── __init__.py
│   ├── main_menu.py        # MainMenu (~200 lines)
│   ├── task.py             # TaskScreen (~80 lines)
│   ├── quick.py            # QuickScreen (~60 lines)
│   ├── downloader.py       # DownloaderScreen (~100 lines)
│   ├── paths.py            # PathsScreen (~80 lines)
│   ├── deps.py             # DepsScreen + InstallScreen (~100 lines)
│   ├── settings.py         # SettingsScreen (~60 lines)
│   └── setup_wizard.py     # SetupWizard (~90 lines)
└── widgets/
    ├── __init__.py
    ├── confirm_dialog.py   # ConfirmDialog (~50 lines)
    └── status_panel.py     # StatusPanel (~40 lines)
```

### Estandarización de interfaces
- Crear protocolos/clases abstractas para:
  - `LrcParser` (parse, write, validate, repair, offset)
  - `LrcFetcher` (search, download)
  - `LyricsExporter` (export a distintos formatos)
  - `LyricsImporter` (import desde distintos formatos)

### Reducción de complejidad
- `core.py` está bien modularizado, pero `config_yaml()` y `config_summary()` podrían migrar a `config.py`
- `process_long_phrases()` en `processor.py` depende de `splitter.py` — bien desacoplado
- Eliminar `LRC_TOOLS_REPO` env var (obsoleto con src/ layout)

---

## FASE 7 — TESTING

### Tests nuevos requeridos

| Archivo | Tests | Prioridad |
|---------|-------|-----------|
| `tests/test_parser.py` | parse_lrc, parse_lrc_simple, write_lrc, format_timestamp | Alta |
| `tests/test_parser_edge.py` | Unicode, BOM, timestamps corruptos, líneas vacías, tags inválidos | Alta |
| `tests/test_processor.py` | process_lrc_file, process_long_phrases, phrases_to_words | Alta |
| `tests/test_splitter.py` | split_phrase_intelligently, find_split_point, find_all_split_points | Alta |
| `tests/test_puller.py` | extract_metadata, extract_metadata_from_filename, _clean_title | Alta |
| `tests/test_puller_mock.py` | search_lrclib (mock HTTP), search_song, resolve_output_path | Media |
| `tests/test_audio.py` | find_audio_for_lrc, find_lrc_for_audio, get_audio_duration (mock) | Alta |
| `tests/test_exporters.py` | roundtrip LRC→SRT→LRC, LRC→JSON→LRC | Media |
| `tests/test_cli.py` | argument parsing, validación de flags | Media |
| `tests/test_config.py` | Config load/save, dataclass defaults | Media |

### Cobertura objetivo
- Líneas críticas (parse, process): >80%
- Líneas totales: >60%

### Comando para medir cobertura
```bash
pip install coverage
coverage run -m unittest discover -s tests
coverage report -m
```

---

## FASE 8 — CALIDAD OPEN SOURCE

### Archivos a crear
- `CONTRIBUTING.md` — guía de contribución (PRs, issues, código de conducta)
- `CHANGELOG.md` — historial de cambios (comenzar con v0.1.0 → v0.2.0)
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `SECURITY.md` — política de seguridad
- `.github/ISSUE_TEMPLATE/` — templates para bug report y feature request
- `.github/PULL_REQUEST_TEMPLATE.md` — template para PRs

### GitHub Actions
- `ci.yml` — ya actualizado con matrix ubuntu/macos/windows
- `release.yml` — ya actualizado con PyInstaller bins
- `.github/workflows/lint.yml` — ruff + mypy + bandit

### Versionado Semántico
- v0.2.0 — actual (src/ layout, deps opcionales)
- v0.3.0 — features nuevas (validate, offset, export)
- v0.5.0 — TUI refactor + tests completos
- v1.0.0 — estable, docs completas, CI/CD verde

---

## FASE 9 — DOCUMENTACIÓN

### README.md — actualizar
- Arreglar rutas `/dev/null/` en code blocks
- Badges: GitHub Actions, PyPI, Python version, license
- Quickstart: "Instalar en 30 segundos"
- Screenshots / asciicast del TUI
- Guía de CLI con ejemplos
- FAQ completa
- Tabla de features y estado

### docs/ — expandir
- `docs/configuration.md` — ya existe, actualizar con nuevas opciones
- `docs/file-formats.md` — ya existe, agregar WLRC, SRT, ASS specs
- `docs/troubleshooting.md` — ya existe, expandir con Windows/macOS
- `docs/api.md` — documentar módulos exportados
- `docs/contributing.md` — cómo contribuir

---

## FASE 10 — ENTREGA FINAL

### Checklist
- [ ] Build limpio (`python -m build`)
- [ ] Tests verdes en CI (Linux, macOS, Windows)
- [ ] Binarios funcionales (PyInstaller)
- [ ] Publicado en PyPI (`pip install lrc-tools`)
- [ ] GitHub Release con assets
- [ ] README actualizado con badges
- [ ] CHANGELOG.md completo
- [ ] CONTRIBUTING.md + CODE_OF_CONDUCT.md
- [ ] `lrc-tools --help` funciona impecable
- [ ] `lrc-fetch --help` funciona impecable
- [ ] `lrc-processor --help` funciona impecable
- [ ] `lrc-vis --help` funciona impecable

### Release workflow
```bash
# 1. Actualizar versión en src/lrc_tools/__init__.py
# 2. Actualizar CHANGELOG.md
# 3. Commit + tag
git commit -m "Release v0.3.0"
git tag v0.3.0
git push origin main --tags
# 4. GitHub Actions build + publish automático
```

### Riesgos pendientes
1. **playerctl en macOS** — necesita brew; el CI lo valida
2. **librosa en Windows** — puede fallar por dependencias nativas (numba, llvmlite). Mitigación: es opcional
3. **syncedlyrics en Windows** — probar en CI de Windows
4. **ffprobe en Windows** — requiere manual PATH config. Mitigación: `choco install ffmpeg`
5. **TUI con Textual en Windows Terminal** — probar compatibilidad
6. **Visualizer en macOS** — playerctl puede no funcionar con Apple Music. Mitigación: mpv --play

---

## RESUMEN DE ARCHIVOS POR FASE

| Fase | Archivos a crear | Archivos a modificar |
|------|-----------------|---------------------|
| F4 | — | cli/fetch.py, cli/process.py, cli/vis.py, tui/app.py, pyproject.toml |
| F5 | exporters.py, importers.py | parser.py, cli/process.py, cli/fetch.py, core.py, config.py |
| F6 | tui/screens/*.py, tui/widgets/*.py | tui/app.py |
| F7 | tests/test_parser.py, tests/test_processor.py, +6 más | tests/__init__.py |
| F8 | CONTRIBUTING.md, CHANGELOG.md, CODE_OF_CONDUCT.md, +5 | .github/workflows/ |
| F9 | — | README.md, docs/*.md |
| F10 | — | __init__.py (version bump) |

> **Total estimado**: ~15 archivos nuevos, ~20 archivos modificados
