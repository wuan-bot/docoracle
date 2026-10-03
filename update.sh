#!/bin/bash
#
uv run docoracle components --antora-root antora-docs --clone
uv run docoracle ingest
