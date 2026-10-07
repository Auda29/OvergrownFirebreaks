# Validation

Local acceptance on 2026-10-07 used Minecraft 1.21.1, NeoForge 21.1.248,
Java 21, Burnt 1.10.5.2 and Overgrown Vegetation 0.1.2.
The standalone server loaded only the two original mods, Cloth Config 15.0.140,
GeckoLib 4.9.3, Player Animation Library 1.1.6, the selected addon modules,
and a test-only acceptance helper. Paxi and TerraVista mods were absent.

| Scenario | Result |
| --- | --- |
| Core only | Passed all 32 mappings and 45 category-tag checks |
| Core with protection | All 336 protected blocks rejected by Overgrown's actual corruption method |
| Remove protection and restart the same generated world | Protection tag removed; default eligibility restored |
| Data reload in each supported scenario | All mappings, category tags and immunity checks passed again |
| Missing Burnt | NeoForge rejects loading with the dependency and required version named |
| Missing Overgrown | NeoForge rejects loading with the dependency and required version named |
| Unsupported Burnt 1.10.5.3 test fixture | Exact-version dependency rejects loading before world startup |
| Protection module without core | NeoForge rejects loading with the missing core dependency named |

Without the protection module, 283 of the 336 selected Burnt blocks were
corruptible under Overgrown's existing rules. The remaining 53 were already
rejected by those rules. None carried the additional immunity tag.
With the module, all 336 carried the tag and were rejected by the actual
`CorruptionRegistry.canCorrupt` method. Ordinary grass remained corruptible.
Hive Node and Overgrown Nexus retained their original fire immunity.

Actual fire converted Overgrown grass into `burnt:smoldering_grass` and
Overgrown logs into `burnt:smoldering_log`. An Overgrown pig corpse and
Overgrown leaves became air. Tests used only generated worlds bound to
`127.0.0.1`; each server process stopped after its scenario.

NeoForge may exit with code zero after reporting a dependency error. The
negative acceptance checks therefore inspect the explicit loading error and
confirm that server and world startup did not occur.

## Client and package checks

Both final addon JARs were installed into the separate TerraVista Overgrowth
profile. The client discovered both modules, initialized the render resources
and sound engine, and remained running until the test harness stopped its own
process. Startup acceptance completed in 44.2 seconds. The normal profile saves
directory contains no generated acceptance worlds.

The previous Paxi rules were moved to a backup outside Paxi's loading directory,
so the installed profile now loads the standalone addon rules. The active
TerraVista profile and its worlds were preserved. Other launcher instance rows
and their file entries were unchanged by the addon installation.

Final packaging checks validate SHA-256 checksums, repeat the build, rebuild from
the extracted source ZIP, and compare the production JARs with those used in
runtime acceptance. JARs contain only original data rules, metadata and license
notices. The test helper and original mods are absent from distributable archives.

## Upstream issues observed

Overgrown 0.1.2 has four rejected smelting/blasting recipes for chlorophyllite
and sap crystal. Its JSON result fields use the wrong format for this game
version. These recipes remain unavailable unless another mod or pack repairs
them. The firebreak addon does not replace these recipes.

Overgrown also logs a malformed `animation.burned.swim` expression through
GeckoLib during client startup. Neither issue blocked the measured fire or
corruption checks. The original mod files were not patched or redistributed.

This acceptance does not cover a full multiplayer client connection, every
infection phase, long survival sessions or shader behavior. Only NeoForge
21.1.248 was exercised; the original dependencies determine the declared
minimum 21.1.150.
