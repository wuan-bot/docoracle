#!/bin/bash
#
uv run qa components --antora-root antora-docs --clone
uv run qa ingest
