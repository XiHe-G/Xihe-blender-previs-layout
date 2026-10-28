# Opt-in contract API

Python 3 + existing jsonschema dependency. Run with an interpreter providing jsonschema (Blender's bundled Python may not). Pure utilities never import bpy or mutate AG/CSP/Blend. `schemas/production-v2.schema.json` is the sole structural definition; `templates/production-v2/*.json` are SYNTHETIC authoring specimens, not approved project data. `effect-parameters.json` is a fragment catalog, not a standalone contract. Existing root templates are unchanged because they own established execution formats; these sidecars add production-level metadata without competing execution timelines.

From skill root:

```powershell
python scripts/production_v2.py validate templates/production-v2/scene-state.json
python scripts/production_v2.py route templates/production-v2/task.json
python scripts/production_v2.py revision templates/production-v2/revision-record.json --shots SH01 SH02 SH03
python scripts/production_v2.py camera templates/production-v2/camera-semantic.json
python scripts/production_v2.py locomotion templates/production-v2/physical-profile.json
python scripts/production_v2.py delivery actual-manifest.json --base actual-package --output compiled-delivery.json
python scripts/production_v2.py handoff actual-handoff.json --manifest actual-manifest.json --output compiled-handoff.json
```

`validate` reports CONTRACT_ONLY. Revision category names describe planned scope, never audit completion. Camera compiler returns a constraint packet, not keyframes. Delivery requires real files and hashes; template zero hashes deliberately cannot certify real output. CLI refuses overwriting output files. Handoff validates against an explicit manifest but does not authenticate rendering or call a provider. Natural-language interpretation, complete cross-document joining, source-authority authentication, automatic physical mapping and production native adapters remain author/future-runtime responsibilities.

Run all tests with `python -B -m unittest discover -s tests -p "test_*.py"`; new tests are `test_production_v2.py`. No legacy script is changed by this layer.
