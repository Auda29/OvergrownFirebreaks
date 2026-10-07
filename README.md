# Overgrown Firebreaks

An independent NeoForge addon that makes selected Overgrown Vegetation blocks
respond to Burnt's fire system. The optional protection addon lets charred ground
serve as a firebreak against block corruption.

This is an alpha. It integrates existing blocks and does not add entities,
textures, weapons, or changes to infection phases.

Download the installation ZIP or individual JARs from
[GitHub Releases](https://github.com/Auda29/OvergrownFirebreaks/releases).
The [German guide](README.de.md) explains installation and the optional protection.

## Supported setup

| Component | Version |
| --- | --- |
| Minecraft | 1.21.1 |
| NeoForge | 21.1.150 or newer in the 21.1 series; tested with 21.1.248 |
| Java | 21 |
| Burnt Basic | 1.10.5.2 |
| Overgrown Vegetation by yayuy_0227 | 0.1.2 |

The alpha requires the exact Burnt and Overgrown versions listed above. A future
version must recheck their block IDs and behavior before widening these ranges.

Install the original mods separately, including their required libraries.
The verified library versions are Cloth Config 15.0.140, GeckoLib 4.9.3 and
Player Animation Library by ZigytheBird 1.1.6. Kosmx's Player Animator is a
different library. The original mods remain responsible for their dependencies.

- [Burnt Basic on Modrinth](https://modrinth.com/mod/burnt-basic)
- [Overgrown Vegetation on CurseForge](https://www.curseforge.com/minecraft/mc-mods/overgrown-vegetation)
- [Overgrown Vegetation source](https://github.com/yayuy-01/overgrown-vegetation)

Do not substitute the unrelated Fabric mod with a similar name.

## Installation

1. Install the supported NeoForge setup and the original mods above.
2. Place `overgrown-firebreaks-0.1.0-alpha.1-neoforge-1.21.1.jar` in `mods`.
3. To protect burnt ground, also place
   `overgrown-firebreaks-protection-0.1.0-alpha.1-neoforge-1.21.1.jar` in `mods`.
4. Restart Minecraft or the server. No Paxi or manual datapack installation is needed.

The installation ZIP contains the core JAR and the protection JAR in `optional`.
Extract it first, then copy the selected JARs into `mods`. Original mods are
not included. Source code is distributed in a separate ZIP.

For the supported multiplayer setup, use matching addon modules on server and
clients. Client startup and a dedicated server are tested separately; a full
multiplayer client connection is not yet part of the acceptance run.

The core addon supports 45 source blocks: 32 convert to Burnt blocks, and 13 vines
or infection corpses are removed by Burnt. Tags are additive with `replace: false`.
The explicit mappings use the `overgrown_firebreaks` namespace. A modpack that
already supplies mappings for the same source blocks must reconcile those rules.

## Optional firebreak protection

The protection JAR adds 336 installed Burnt block IDs to
`overgrown_vegetation:corruption_immune`. These include burnt, sooty, smoldering,
blazing and ember remnants. The protection applies to remnants created by any
fire, including burnt building materials. It can make charred bases much safer.

For compatibility alone, install only the core JAR. To enable the protection,
install both JARs. To disable it, remove only the protection JAR and restart.
It adds no blocks or entities, so removing it leaves existing blocks intact.
Once grass regrows into ordinary Minecraft grass, that grass is infectable again.

The immunity tag blocks Overgrown's block-corruption path. It does not suppress
spores, stop biome corruption, cure infected creatures or remove infection sources.
Hive Nodes and Overgrown Nexus retain their original fire immunity. Use Overgrown's
own countermeasures to handle those sources.

The core rules do not indiscriminately burn infected stone, ores, machinery,
husk containers or aquatic plants.

Without this optional module, Overgrown's own block eligibility rules still
apply. Some non-solid remnants are already rejected by those rules; removing
the module removes our added immunity rather than forcing every block to infect.

## Build

Run `python build.py` with Python 3.11 or newer. This project uses NeoForge's
`lowcodefml` loader, so it does not need a Java compiler or Gradle to build.
The reproducible JARs, installation ZIP, source ZIP and SHA-256 checksums appear in `dist`.

The project source is MIT licensed. The original mods and assets are not bundled.
See `NOTICE` for credits and scope of the license.

GitHub Actions builds and checks the distributable packages on Windows and Linux.
Run `python tests/verify_packages.py` to check checksums, package contents,
repeatability and rebuilding from the source ZIP locally. Minecraft runtime
acceptance is a separate local test requiring the original mods.

## Verification and known limits

Runtime acceptance uses a generated local test world and checks the actual
Burnt mapping registry and Overgrown corruption method. It tests core-only and
core-plus-protection behavior, real fire conversion, datapack reload, and missing
dependency errors. Test Java code is never packaged in the production JARs.
See `tests/README.md` and the local verification report for measured results.
The shareable summary is in `VALIDATION.md`.

Overgrown 0.1.2 logs a malformed `animation.burned.swim` expression through
GeckoLib during client startup. It does not prevent the tested client startup
or the server-side integration. This addon does not patch the original animation.
Overgrown also ships four invalid smelting/blasting recipes for chlorophyllite
and sap crystal. Those upstream recipes fail to load; this addon leaves them
unchanged. See the validation notes for the exact scope.

Long survival sessions, every infection phase and shader behavior are not covered
by these integration checks. The build script creates local artifacts; release
publication is a separate step.
