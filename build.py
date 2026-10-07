"""Build deterministic, data-only NeoForge addon JARs using Python 3.11+."""
from pathlib import Path
import hashlib
import json
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION = "0.1.0-alpha.1"
SUFFIX = f"{VERSION}-neoforge-1.21.1"
MODULES = {"main": "overgrown-firebreaks", "protection": "overgrown-firebreaks-protection"}


def normalized_bytes(path):
    # Git checkouts and Windows editors may use different line endings.
    # Every source/resource file in this project is text; normalize before packing.
    return path.read_bytes().replace(b"\r\n", b"\n")


def archive(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as jar:
        for name, content in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            jar.writestr(item, content)


def build():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    artifacts = []
    for module, name in MODULES.items():
        resources = ROOT / "src" / module / "resources"
        metadata = tomllib.loads((resources / "META-INF/neoforge.mods.toml").read_text("utf8"))
        assert metadata["modLoader"] == "lowcodefml"
        assert metadata["mods"][0]["version"] == VERSION
        entries = {p.relative_to(resources).as_posix(): normalized_bytes(p)
                   for p in resources.rglob("*") if p.is_file()}
        for path, content in entries.items():
            if path.endswith(".json") or path == "pack.mcmeta":
                json.loads(content)
            assert not path.endswith((".class", ".jar", ".png", ".ogg")), path
        entries["LICENSE"] = normalized_bytes(ROOT / "LICENSE")
        entries["NOTICE"] = normalized_bytes(ROOT / "NOTICE")
        entries["META-INF/MANIFEST.MF"] = (
            f"Manifest-Version: 1.0\r\nImplementation-Version: {VERSION}\r\n\r\n"
        ).encode("utf8")
        output = dist / f"{name}-{SUFFIX}.jar"
        archive(output, entries)
        artifacts.append(output)
    install_entries = {
        artifacts[0].name: artifacts[0].read_bytes(),
        "optional/" + artifacts[1].name: artifacts[1].read_bytes(),
        "README.md": normalized_bytes(ROOT / "README.md"),
        "README.de.md": normalized_bytes(ROOT / "README.de.md"),
        "LICENSE": normalized_bytes(ROOT / "LICENSE"),
        "NOTICE": normalized_bytes(ROOT / "NOTICE"),
        "INSTALL.txt": (
            "Overgrown Firebreaks " + VERSION + "\n\n"
            "Deutsch: ZIP entpacken. Die Haupt-JAR in mods kopieren. Fuer geschuetzte\n"
            "Brandflaechen zusaetzlich die JAR aus optional in mods kopieren.\n"
            "Originalmods und Bibliotheken separat installieren. Siehe README.de.md.\n\n"
            "English: Extract this ZIP. Copy the main JAR into mods. To enable\n"
            "firebreak protection, also copy the JAR from optional into mods.\n"
            "Install the original mods and their libraries separately. See README.md.\n"
        ).encode("utf8"),
    }
    if (ROOT / "VALIDATION.md").is_file():
        install_entries["VALIDATION.md"] = normalized_bytes(ROOT / "VALIDATION.md")
    install_entries["SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(content).hexdigest()}  {name}\n"
        for name, content in sorted(install_entries.items()) if name.endswith(".jar")
    ).encode("utf8")
    output = dist / f"overgrown-firebreaks-{VERSION}-install.zip"
    archive(output, install_entries)
    artifacts.append(output)
    # Source bundle contains only this project's own files, never installed mods,
    # launcher metadata, server libraries, worlds, logs, or local test settings.
    source_files = [ROOT / n for n in ["build.py", "README.md", "README.de.md", "LICENSE",
                                      "NOTICE", "CHANGELOG.md", ".gitignore", ".gitattributes"]]
    source_files += [p for p in [ROOT / "VALIDATION.md"] if p.is_file()]
    source_files += [p for base in [ROOT / "src", ROOT / "tests", ROOT / ".github"]
                     for p in base.rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.suffix in {".java", ".py", ".json", ".toml", ".mcmeta", ".md", ".yml"}]
    output = dist / f"overgrown-firebreaks-{VERSION}-sources.zip"
    archive(output, {f"OvergrownFirebreaks/{p.relative_to(ROOT).as_posix()}": normalized_bytes(p)
                     for p in source_files})
    artifacts.append(output)
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in artifacts)
    (dist / "SHA256SUMS.txt").write_text(sums, encoding="utf8", newline="\n")
    for p in artifacts:
        print(f"BUILT {p.name} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
