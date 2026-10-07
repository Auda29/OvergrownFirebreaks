# Runtime acceptance

`AddonVerification.java` is a test-only NeoForge mod. It calls the installed
mods' real mapping and corruption methods after the server starts. It also
rechecks those methods after a data reload when the harness writes
`verify-again.flag` in the generated server directory.
The local harness currently targets Windows and NeoForge's `win_args.txt`.

The helper checks all 32 explicit mappings, all 45 category-tag memberships,
all 336 Burnt remnants with and without protection, ordinary grass, and the
original fire immunity of Hive Node and Overgrown Nexus. It is never included
in either production JAR.

The local harness `verify_runtime.py` accepts explicit paths to the installed
mods, a prepared NeoForge 21.1.248 server library directory, Java 21, and a
Java 21 compiler. It creates only generated test directories beneath
`.verification` and binds its server to `127.0.0.1`. It does not download or
redistribute the original mods. A source ZIP contains this test code and the
expectations, but never the local test installation.

Acceptance scenarios cover core only, core plus protection, a restart without
the protection module using the previously tested world, missing Burnt,
missing Overgrown, an unsupported Burnt version, and missing core with only
the protection addon. Real grass, log, corpse and leaves fire tests run with
the full integration enabled. A reload must preserve all mappings and tags.

Client resource, sound and render startup is checked separately in the isolated
TerraVista Overgrowth profile. This does not claim a tested multiplayer client
connection, full survival playthrough, or shader acceptance.
