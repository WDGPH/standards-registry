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

