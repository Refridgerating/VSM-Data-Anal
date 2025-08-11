# VSM-Data-Anal
A GUI-based toolkit for importing, visualizing, and analyzing Vibrating Sample Magnetometry (VSM) datasets. Designed for fast multi-file plotting (superimposed or side‑by‑side), publication‑quality graph exports, and one‑click extraction of key magnetic parameters (e.g., saturation magnetization, coercivity, remanence, anisotropy constants). Includes tools for paramagnetic background subtraction and unit conversions with guided prompts.

Status: Initial spec & scaffolding for Codex/agent-driven implementation.
Target audience: Experimentalists working with VSM hysteresis and M(H/T) data.

## Quick workflow

1. **Load data** – choose one or more CSV files via *File → Open*.
2. **Pick axes** – select the X and Y columns once; the choice is reused for every file.
3. **Toggle layout** – switch between *Superimposed* and *Side-by-Side* views from the *View → Layout* menu.
4. **Inspect** – compare curves, zoom and pan, then export figures as needed.

This sequence makes for a concise, GIF-worthy demonstration of the plotting interface.

Key Features
GUI-first workflow

File picker with multi-select; drag‑and‑drop support.

Plot multiple datasets superimposed or in side‑by‑side panes.

Choose x/y axes from file headers; set axis ranges, scales (linear/log), limits, and labels.

Standard plot controls: line style/width, markers, color cycling, legends, grid, minor ticks.

Interactive zoom/pan/reset; toggle datasets and fit overlays.

Export plots to PNG, SVG, PDF; export processed data and fit results to CSV/JSON.

Project files (.vsmproj, JSON) to save/restore sessions (files, styles, fits, views).

Flexible data ingestion

CSV/TSV and common vendor formats (e.g., Quantum Design, Lakeshore) via parser plugins.

Header autodetect with manual override and mapping UI.

Analysis & fitting

Saturation magnetization (Ms):

High-field linear fit & extrapolation or plateau averaging.

Unit-aware conversion (emu → A/m, emu/g → A·m²/kg), with prompts for sample geometry, mass, density, dimensions.

Coercivity (Hc):

Zero-crossing interpolation on ascending/descending branches; optional smoothing.

Remanent magnetization (Mr):

Intercept at H=0 with spline/linear interpolation.

Anisotropy constants (e.g., Ku):

Sucksmith–Thompson method (plot M/H vs M²; linear fit → Ku).

Optional hard/easy axis energy method (requires angle/geometry inputs).

Prompts for demagnetizing factors (shapes: thin film, rod, sphere) and orientation.

Paramagnetic background subtraction:

High-field χ·H linear tail fit & subtract (select field window).

Optional Langevin/Brillouin fit for superparamagnetic contributions.

Before/after comparison overlay; residual diagnostics.

Batch processing

Apply the same axis/fit/export settings to multiple files at once.

Generate parameter tables (Ms, Hc, Mr, Ku, χ) across datasets.

Reproducibility

All fits/inputs recorded in project metadata; one-click report export (PDF/Markdown).

Screenshots (placeholders)
docs/img/import-dialog.png

docs/img/superimposed-plots.png

docs/img/side-by-side.png

docs/img/anisotropy-fit.png

(Add after first build.)

Data Expectations
Typical VSM headers the app can map automatically (case-insensitive):

Field, H, Magnetic Field (Oe/T), Applied Field

Moment, M (emu), Magnetization (emu/g, emu/cm^3, A/m)

Time, Temperature, Sweep #

Users can reassign columns in the Axis Mapping panel. Mixed-unit files are supported with per-column unit tags.

Installation
Prerequisites
Python 3.10+

Recommended: a virtual environment (venv or conda)

Dependencies
Declared in pyproject.toml / requirements.txt:

GUI: PyQt6 (or qtpy as abstraction)

Plotting: matplotlib

Data: pandas, numpy

Fitting: scipy, lmfit (optional but recommended)

Units: pint

Config/IO: pydantic, ruamel.yaml (optional)

Export: reportlab (for PDF report), jinja2 (templated reports)

Install:

bash
Copy
Edit
pip install -r requirements.txt
# or
pipx runpip vsm-gui install -r requirements.txt
Run (dev):

bash
Copy
Edit
python -m vsm_gui
Repository Layout
bash
Copy
Edit
vsm-gui/
├─ src/
│  └─ vsm_gui/
│     ├─ __init__.py
│     ├─ app.py                # Entry point (Qt application bootstrap)
│     ├─ main_window.py        # Menus, toolbar, status bar, split views
│     ├─ file_io/
│     │  ├─ loader.py          # Generic CSV/TSV loader, header detection
│     │  ├─ parsers/
│     │  │  ├─ base.py         # Parser interface
│     │  │  ├─ lakeshore.py
│     │  │  └─ qd_ppms.py
│     ├─ widgets/
│     │  ├─ file_picker.py     # Multi-select & drag/drop
│     │  ├─ axis_mapping.py    # Choose headers, units, scales, ranges
│     │  ├─ plot_pane.py       # Matplotlib canvas + toolbar
│     │  ├─ style_panel.py     # Colors, markers, line styles
│     │  ├─ analysis_panel.py  # Ms/Hc/Mr/Ku, paramag subtraction controls
│     │  ├─ batch_panel.py     # Apply settings to many files
│     │  └─ prompts.py         # Guided input dialogs (mass, dims, density, etc.)
│     ├─ plotting/
│     │  ├─ manager.py         # Tracks figures, layers, superimposed vs side-by-side
│     │  ├─ themes.py          # Light/dark, journal presets
│     │  └─ exporters.py       # PNG/SVG/PDF, CSV/JSON data export
│     ├─ analysis/
│     │  ├─ metrics.py         # Hc, Mr, Ms algorithms
│     │  ├─ anisotropy.py      # Sucksmith–Thompson & related methods
│     │  ├─ paramag.py         # χ·H tail, Langevin/Brillouin fits
│     │  ├─ smoothing.py       # Savitzky–Golay, rebinning, outlier removal
│     │  └─ demag.py           # Shape demagnetizing factors
│     ├─ units/
│     │  ├─ registry.py        # Pint unit registry; conversions
│     │  └─ conversions.py     # emu ↔ A·m², emu/cm³ ↔ A/m, etc.
│     ├─ project/
│     │  ├─ model.py           # .vsmproj schema (pydantic)
│     │  └─ io.py              # Save/load project state
│     ├─ reports/
│     │  ├─ builder.py         # PDF/Markdown report generator
│     │  └─ templates/         # Jinja2 templates
│     └─ utils/
│        ├─ logging.py
│        └─ errors.py
├─ tests/
│  ├─ test_parsers.py
│  ├─ test_metrics.py
│  ├─ test_anisotropy.py
│  └─ test_paramag.py
├─ examples/
│  ├─ data/                    # Sample CSVs (loop, high-field segments)
│  └─ projects/                # Example .vsmproj files
├─ docs/
│  ├─ img/
│  └─ user-guide.md
├─ pyproject.toml
├─ requirements.txt
├─ README.md
└─ LICENSE
Usage Overview
1) Import Data
File → Import… (multi-select) or drag & drop into the file list.

The Axis Mapping dialog appears:

Pick X and Y from detected headers (e.g., Field (Oe) vs Moment (emu)).

Set units (Oe/T, emu, emu/g, emu/cm³, A/m), scale (linear/log), and axis ranges.

Save as default mapping for that vendor format.

2) Plotting
Choose Superimposed or Side-by-Side in the toolbar.

Adjust styles (line/marker/width), toggle legends/grid/ticks.

Zoom/pan with the embedded toolbar; right‑click to reset view.

3) Analysis
Ms: Select a high-field window; choose Linear Extrapolation or Plateau.

If units require volume/mass: a guided prompt asks for mass (g), density (g/cm³), dimensions, or thickness & area (for films).

Hc: The app finds M=0 crossings on both branches; view values and confidence.

Mr: Intercept at H=0 with optional spline interpolation.

Ku (Sucksmith–Thompson): The app builds M/H vs M², fits a line, derives Ku.

Prompts for demag correction and geometry (thin film, rod, sphere); optional angle.

Paramagnetic subtraction: Select a high-field range; fit M = χ·H + b (or Langevin).

Preview subtraction; export residuals and fit parameters.

Batch mode: Apply chosen operations to all selected files and export a summary table.

4) Export
Plots: PNG/SVG/PDF with DPI and size controls; journal presets (PRB, APL, etc.).

Data: CSV of processed curves; JSON with fit parameters & uncertainties.

Reports: One-click PDF/Markdown including figures, tables, and method notes.

Algorithms & Assumptions (Brief)
Hc: Linear/spline interpolation between nearest sign-change points on each branch; optional detrend/smoothing (Savitzky–Golay).

Mr: Evaluate M at H=0 using spline/linear interpolation of nearest points.

Ms:

Linear high-field extrapolation of M(H) to infinite field; slope gives χ, intercept → Ms.

Plateau averaging over user-defined top/bottom field windows.

Ku (Sucksmith–Thompson): Fit of M/H vs M² yields slope/intercept related to Ku (details in in-app docs). Demag corrections applied if geometry provided.

Paramag subtraction: Fit in |H| ≥ H_min region for χ (and b); subtract χ·H (+b) from full curve. Optional Langevin/Brillouin model for SP-MNPs.

Each result includes fit ranges, R²/χ², confidence intervals when available.

Configuration
Settings file: ~/.vsm-gui/config.yaml

Default plot theme, fonts, journal presets

Default unit system (SI/CGS)

Vendor header mappings

Project file: .vsmproj (JSON) stores:

File paths (relative), axis choices, unit preferences

Plot styles and layouts

Analysis steps, fit windows, results, and notes

Extensibility
Parsers: Implement file_io/parsers/base.py interface and register entry point.

Analyses: Add a function under analysis/ returning values + uncertainties (+ metadata) and register with the Analysis panel.

Themes: Add plot style profiles under plotting/themes.py.

Testing
Run unit tests:

bash
Copy
Edit
pytest -q
Suggested fixtures in examples/data/:

Symmetric loop with known Ms/Hc/Mr

Anisotropy dataset for Sucksmith–Thompson validation

High-field segment for paramag subtraction tests

Roadmap
ROI tools for partial-loop analysis (first quadrant, FORC preparation)

Temperature-dependent M(T) analysis with Curie/Blocking fits

Angle-dependent anisotropy workflows

Column math (normalize by mass/volume/film area)

Live LaTeX labels in plots

SQUID/VSM mixed-mode parser plugins

Command-line batch pipeline (headless)

Contributing
PRs welcome! Please:

Open an issue describing the feature/bug.

Add tests and docs.

Follow the existing code style (black/ruff/mypy if enabled).

License
MIT License

Citation
If this tool contributes to a publication, please cite the repository (CITATION.cff to be added).

A Note on Units
The app uses SI internally via pint. Inputs in CGS (emu, Oe) are accepted and converted with explicit prompts. Users will be guided to supply either mass & density or geometric dimensions to compute volume/mass‑normalized quantities.
