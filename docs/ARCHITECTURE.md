# Architecture Overview

This project provides a light‑weight framework for viewing and analysing VSM
(data).  The refactor introduces three key extension points:

## Dataset model

`vsm_gui.model.Dataset` wraps a pandas `DataFrame` together with metadata such
as column names and units.  It offers helpers like `select_xy()` which validates
and cleans numeric columns and `clone()` for copying datasets.  Plotting code
and analyses use this typed object instead of raw frames.

## Parser plugins

File readers implement the `ParserPlugin` protocol
(`vsm_gui.file_io.parsers`).  Plugins register themselves via
`register()` and are discovered by `load_any()`.  The built‑in CSV parser is an
example; new formats can be supported by providing a module that implements the
protocol and calls `register` when imported.

## Services

Utility services under `vsm_gui.services` centralise domain logic.  The initial
`units` service performs numeric coercion and acts as a placeholder for future
unit conversion features.

These components decouple data loading, analysis and rendering, making it easy
to add new file types, analyses or plotting modes without touching existing
code.
