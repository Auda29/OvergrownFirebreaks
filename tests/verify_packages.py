"""Verify complete, reproducible distribution packages without original mods."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digests(path):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.iterdir() if p.is_file()}


def main():
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)
    dist = ROOT / "dist"
    expected = digests(dist)
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)
    assert digests(dist) == expected, "Repeated build differs"
    for line in (dist / "SHA256SUMS.txt").read_text("utf8").splitlines():
        digest, name = line.split("  ", 1)
        assert expected[name] == digest
    jars = sorted(dist.glob("*.jar"))
    assert len(jars) == 2
    for path in jars:
        with zipfile.ZipFile(path) as jar:
            names = jar.namelist()
            assert not any(n.endswith((".class", ".jar", ".png", ".ogg")) for n in names)
            meta = tomllib.loads(jar.read("META-INF/neoforge.mods.toml").decode("utf8"))
            assert meta["modLoader"] == "lowcodefml"
            assert meta["license"] == "MIT"
            identifier = meta["mods"][0]["modId"]
            dependencies = {d["modId"]: d for d in meta["dependencies"][identifier]}
            assert dependencies["minecraft"]["versionRange"] == "[1.21.1]"
            assert dependencies["burnt"]["versionRange"] == "[1.10.5.2]"
            assert dependencies["overgrown_vegetation"]["versionRange"] == "[0.1.2]"
            if identifier == "overgrown_firebreaks":
                mappings = json.loads(jar.read("data/overgrown_firebreaks/burn_mappings/overgrowth.json"))["mappings"]
                assert len(mappings) == 32 and len({x["from"] for x in mappings}) == 32
                assert not any("corruption_immune" in n for n in names)
            elif identifier == "overgrown_firebreaks_protection":
                immune = json.loads(jar.read("data/overgrown_vegetation/tags/block/corruption_immune.json"))
                assert immune["replace"] is False and len(set(immune["values"])) == 336
                assert dependencies["overgrown_firebreaks"]["versionRange"] == "[0.1.0-alpha.1]"
            else:
                raise AssertionError("Unexpected addon " + identifier)
    with tempfile.TemporaryDirectory(prefix="firebreaks-packages-") as temporary:
        target = Path(temporary)
        source = next(dist.glob("*-sources.zip"))
        with zipfile.ZipFile(source) as archive:
            for name in archive.namelist():
                assert (target / name).resolve().is_relative_to(target.resolve())
                assert ".verification" not in name and "app.db" not in name
                assert not name.endswith((".jar", ".class", ".png", ".ogg"))
            archive.extractall(target)
        rebuilt = target / "OvergrownFirebreaks"
        subprocess.run([sys.executable, str(rebuilt / "build.py")], check=True)
        assert digests(rebuilt / "dist") == expected, "Source ZIP roundtrip differs"
    print("PASS: checksums, package contents, repeated build and source ZIP roundtrip")


if __name__ == "__main__":
    main()
