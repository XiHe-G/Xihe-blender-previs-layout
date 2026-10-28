"""Offline validation for S45 auxiliary schemas; no registry/network fetches."""
from pathlib import Path
from copy import deepcopy
from jsonschema import Draft202012Validator
from referencing import Registry,Resource
from s2_common import read,digest

SCHEMAS=['repair-feasibility.schema.json','repair-impact-graph.schema.json','motion-boundary.schema.json','authorized-discontinuity.schema.json','repair-assessment.schema.json']
def validate_protocol(value,name):
    if name not in SCHEMAS:raise ValueError('UNKNOWN_S45_PROTOCOL')
    root=Path(__file__).resolve().parents[1]/'authoring';resources={}
    for n in SCHEMAS:
        schema=deepcopy(read(root/n));schema['$id']=(root/n).as_uri();resources[n]=schema
    registry=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in resources.values()])
    Draft202012Validator(resources[name],registry=registry).validate(value);digest(value)
    return True
