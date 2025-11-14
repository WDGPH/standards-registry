# Standards Registry

NOTE: This is a living registry. Please expect the content of this document to change in the coming weeks while it is populated and trialled.

This repository provides a version-controlled registry of standards that are used across WDGPH's automation and data engineering projects. 

It provides a *single source of truth* for maintaining consistent schemas, naming conventions, validation rules, and reference metadata across systems, teams, and environments. 

By hosting standards in Git and referencing them as submodules, this registry ensures: 

* Reproducibility and traceabiltiy of all standards used in data pipelines 
* Controlled versioning with semantic tags (e.g. `v1.0.0`, `v1.1.0`)
* Transparent collaboration and peer review through GitHub
* Easy integration with validation tools, scripts, and CI/CD workflows.

## Structure

`registry.yaml`: Machine-readable file describing standards and their versions

`data-standards/`: XML, YAML, and JSON schemas that define data formats and interoperability requirements

## Integration

Projects can include this registry as a Git submodule to ensure that they use the correct, version-pinned standards. This can be done in bash or in python, with examples to be added.

## Web Interface (Gradio)

A modern web interface is available for browsing and searching the Standards Registry.

### Features

- **Registry Overview**: View all standards with statistics
- **Browse Standards**: Explore individual standards with detailed information
- **View Data**: Interactive tables for viewing all records with horizontal scrolling support
- **Search Records**: Full-text search across standard records

### Installation

Using `uv` (recommended):

```bash
uv sync
```

Or using `pip`:

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python standards_registry.py
```

The application will start on `http://localhost:7860` by default (or `http://0.0.0.0:7860` for network access).

### Usage

1. **Registry Overview**: See all standards at a glance with record counts
2. **Browse Standards**: Select a standard from the dropdown to view:
   - Standard metadata (ID, version, maintainer, etc.)
   - Statistics (total records, fields)
   - Data preview
3. **View Data**: Load complete data tables for any standard with resizable columns and horizontal scrolling
4. **Search Records**: Search for specific terms across all records in a standard

### Architecture

- `StandardsRegistry`: Main class for loading and managing standards
- `Standard`: Dataclass representing a single standard
- Gradio Blocks interface with multiple tabs for different views
