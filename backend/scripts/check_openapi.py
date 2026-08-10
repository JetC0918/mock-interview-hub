"""Fail CI when runtime OpenAPI and the committed artifact drift."""
from generate_openapi import OUTPUT, rendered


if OUTPUT.read_text(encoding="utf-8") != rendered():
    raise SystemExit("OpenAPI drift detected; run scripts/generate_openapi.py and regenerate the frontend client")
print("OpenAPI artifact matches runtime schema")
