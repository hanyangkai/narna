from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def schemas_dir() -> Path:
    here = Path(__file__).resolve().parent
    bundled = here / "_spec_schemas"
    if (bundled / "agent-spec.schema.json").exists():
        return bundled
    for parent in [here, *here.parents]:
        candidate = parent / "specs" / "schemas"
        if (candidate / "agent-spec.schema.json").exists():
            return candidate
    raise FileNotFoundError("UAP schemas not found (expected bundled _spec_schemas or specs/schemas)")


def load_schema(name: str) -> dict[str, Any]:
    path = schemas_dir() / name
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def schema_registry() -> Registry:
    registry = Registry()
    for path in sorted(schemas_dir().glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if not schema_id:
            continue
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))
    return registry


def validator_for(name: str) -> Draft202012Validator:
    schema = load_schema(name)
    return Draft202012Validator(schema, registry=schema_registry())
