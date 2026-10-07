"""Acceptance against local NeoForge and original mods; no downloads or uploads."""
from pathlib import Path
import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import time
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-alpha.1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mods", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--javac", type=Path, required=True)
    parser.add_argument("--port", type=int, default=25589)
    parser.add_argument("--resume", type=Path, help="Resume a partial local acceptance session")
    opts = parser.parse_args()
    session = opts.resume.resolve() if opts.resume else PROJECT / ".verification" / time.strftime("%Y%m%d-%H%M%S")
    assert session.resolve().is_relative_to((PROJECT / ".verification").resolve())
    session.mkdir(parents=True, exist_ok=bool(opts.resume))
    libraries = opts.server.resolve() / "libraries"
    launch = libraries / "net/neoforged/neoforge/21.1.248/win_args.txt"
    raw = shlex.split(launch.read_text("utf8"), posix=True)
    args = [x.replace("-DlibraryDirectory=libraries", "-DlibraryDirectory=" + libraries.as_posix())
             .replace("libraries/", libraries.as_posix() + "/") for x in raw]
    launch_args = session / "server.args"
    launch_args.write_text("\n".join(json.dumps(x) for x in args), encoding="utf8")
    classes = session / "classes"
    classes.mkdir(exist_ok=bool(opts.resume))
    # The Java helper uses reflection for Minecraft and original-mod APIs.
    cp = ";".join(p.as_posix() for p in libraries.rglob("*.jar"))
    javac_args = session / "javac.args"
    javac_args.write_text("\n".join(json.dumps(x) for x in [
        "-proc:none", "-encoding", "UTF-8", "-classpath", cp, "-d", classes.as_posix(),
        (PROJECT / "tests/AddonVerification.java").as_posix()]), encoding="utf8")
    subprocess.run([str(opts.javac), "@" + str(javac_args)], check=True)
    helper = session / "acceptance-helper-test-only.jar"
    with zipfile.ZipFile(helper, "w") as jar:
        for file in classes.rglob("*.class"):
            jar.write(file, file.relative_to(classes).as_posix())
        jar.writestr("META-INF/neoforge.mods.toml", '''modLoader="javafml"
loaderVersion="[4,)"
license="MIT"
[[mods]]
modId="overgrown_firebreaks_verification"
version="1.0.0"
displayName="Firebreaks acceptance helper - TEST ONLY"
''')
    required = {"burnt", "overgrown_vegetation", "cloth_config", "geckolib", "player_animation_library"}
    originals = {}
    import tomllib
    for file in opts.mods.glob("*.jar"):
        with zipfile.ZipFile(file) as jar:
            if "META-INF/neoforge.mods.toml" not in jar.namelist():
                continue
            meta = tomllib.loads(jar.read("META-INF/neoforge.mods.toml").decode("utf8"))
            for mod in meta.get("mods", []):
                if mod["modId"] in required:
                    assert mod["modId"] not in originals, "Duplicate original mod"
                    originals[mod["modId"]] = file
    assert originals.keys() == required, required - originals.keys()
    dist = PROJECT / "dist"
    core = dist / f"overgrown-firebreaks-{VERSION}-neoforge-1.21.1.jar"
    protection = dist / f"overgrown-firebreaks-protection-{VERSION}-neoforge-1.21.1.jar"
    report = {"versions": {"minecraft": "1.21.1", "neoforge": "21.1.248",
                           "burnt": "1.10.5.2", "overgrown": "0.1.2", "addon": VERSION},
              "scenarios": [], "production_mods_require_paxi": False}
    artifact_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (core, protection)}
    if opts.resume:
        report = json.loads((session / "report.json").read_text("utf8"))
        assert report.get("artifact_sha256") == artifact_hashes, "Addon binaries changed; start a fresh acceptance session"
    report["artifact_sha256"] = artifact_hashes

    def passed(name):
        return any(x["name"] == name and x["result"] == "PASS" for x in report["scenarios"])

    def prepare(name, include_protection=False, omit=None, include_core=True, negative=False):
        case = session / name
        case.mkdir(exist_ok=bool(opts.resume))
        mods = case / "mods"
        mods.mkdir(exist_ok=bool(opts.resume))
        for identifier, file in originals.items():
            if identifier != omit:
                shutil.copy2(file, mods / file.name)
        if include_core:
            shutil.copy2(core, mods / core.name)
        if include_protection:
            shutil.copy2(protection, mods / protection.name)
        if not negative:
            shutil.copy2(helper, mods / helper.name)
        (case / "eula.txt").write_text("eula=true\n", encoding="utf8")
        (case / "server.properties").write_text(
            f"server-ip=127.0.0.1\nserver-port={opts.port}\nonline-mode=false\n"
            "level-name=generated_acceptance_world\nlevel-type=minecraft:flat\n"
            'generator-settings={"biome":"minecraft:plains","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}]}\n'
            "generate-structures=false\nview-distance=2\nsimulation-distance=2\n"
            "max-players=1\ndifficulty=peaceful\nspawn-protection=0\n", encoding="utf8")
        return case

    def run(case, protected=False, negative=None, name=None, fire=False, reload=False):
        label = name or case.name
        print("RUN " + label, flush=True)
        log = case / (label + ".log")
        if (case / "verification-results.txt").exists():
            (case / "verification-results.txt").unlink()
        with log.open("w", encoding="utf8") as output:
            process = subprocess.Popen([str(opts.java), "-Xms256m", "-Xmx2048m",
                "-Dfirebreaks.protection=" + str(protected).lower(),
                "-Dfirebreaks.expectations=" + (PROJECT / "tests/expectations.json").as_posix(),
                "@" + str(launch_args), "nogui"], cwd=case, stdout=output,
                stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW)
            (case / "process.json").write_text(json.dumps({"pid": process.pid, "test_only": True}), encoding="utf8")

            def send(command):
                process.stdin.write(command + "\n")
                process.stdin.flush()

            def wait_for(predicate, seconds=120):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    content = log.read_text("utf8", errors="replace")
                    if predicate(content):
                        return content
                    if process.poll() is not None:
                        raise AssertionError(f"{label}: exited {process.returncode}; see {log}")
                    time.sleep(0.5)
                raise AssertionError(f"{label}: timed out; see {log}")

            try:
                if negative:
                    process.wait(timeout=75)
                    content = log.read_text("utf8", errors="replace")
                    assert "Missing or unsupported mandatory dependencies" in content, content[-3000:]
                    assert negative in content, content[-3000:]
                    assert "Starting minecraft server version" not in content and "Done (" not in content
                    report["scenarios"].append({"name": label, "result": "PASS", "rejected_dependency": negative,
                                                "exit_code": process.returncode})
                else:
                    wait_for(lambda s: "FIREBREAKS_VERIFICATION PASS" in s or "FIREBREAKS_VERIFICATION FAIL" in s)
                    checks = (case / "verification-results.txt").read_text("utf8")
                    assert "RESULT PASS" in checks, checks
                    wait_for(lambda s: 'Done (' in s)
                    entry = {"name": label, "result": "PASS", "checks": checks.splitlines()}
                    if fire:
                        send("gamerule doMobSpawning false")
                        send("gamerule randomTickSpeed 20")
                        send("forceload add 0 0 15 15")
                        for x, block in [(0, "overgrown_grass_block"), (4, "overgrown_log"),
                                         (8, "overgrown_pig_corpse"), (12, "overgrown_leaves")]:
                            send(f"setblock {x} 64 0 minecraft:stone")
                            send(f"setblock {x} 65 0 overgrown_vegetation:{block}")
                            send(f"setblock {x} 66 0 minecraft:fire")
                        deadline = time.monotonic() + 60
                        while time.monotonic() < deadline:
                            (case / "fire-check.flag").touch()
                            time.sleep(3)
                            if "FIREBREAKS_FIRE PASS" in log.read_text("utf8", errors="replace"):
                                break
                        assert "FIREBREAKS_FIRE PASS" in log.read_text("utf8", errors="replace"), (case / "fire-results.txt").read_text("utf8")
                        entry["real_fire"] = (case / "fire-results.txt").read_text("utf8").splitlines()
                    if reload:
                        before = log.read_text("utf8", errors="replace").count("advancements")
                        send("reload")
                        wait_for(lambda s: s.count("advancements") > before)
                        count = log.read_text("utf8", errors="replace").count("FIREBREAKS_VERIFICATION PASS")
                        (case / "verify-again.flag").touch()
                        wait_for(lambda s: s.count("FIREBREAKS_VERIFICATION PASS") > count or "FIREBREAKS_VERIFICATION FAIL" in s)
                        checks = (case / "verification-results.txt").read_text("utf8")
                        assert "RESULT PASS" in checks, checks
                        entry["data_reload"] = "PASS"
                    send("stop")
                    process.wait(timeout=45)
                    assert process.returncode == 0
                    report["scenarios"].append(entry)
                print("PASS " + label, flush=True)
            finally:
                if process.poll() is None:
                    try:
                        send("stop")
                        process.wait(timeout=15)
                    except (OSError, subprocess.TimeoutExpired):
                        process.terminate()
                        process.wait(timeout=15)
            (session / "report.json").write_text(json.dumps(report, indent=2), encoding="utf8")

    if not passed("core-only"):
        run(prepare("core-only"), reload=True)
    if not passed("with-protection"):
        run(prepare("with-protection", include_protection=True), protected=True, fire=True, reload=True)
    if not passed("protection-removed-same-world"):
        with_protection = session / "with-protection"
        addon = with_protection / "mods" / protection.name
        assert addon.resolve().is_relative_to(session.resolve())
        assert addon.with_suffix(".jar.disabled").resolve().is_relative_to(session.resolve())
        addon.rename(addon.with_suffix(".jar.disabled"))
        run(with_protection, name="protection-removed-same-world", reload=True)
    if not passed("missing-burnt"):
        run(prepare("missing-burnt", omit="burnt", negative=True), negative="burnt")
    if not passed("missing-overgrown"):
        run(prepare("missing-overgrown", omit="overgrown_vegetation", negative=True), negative="overgrown_vegetation")
    if not passed("unsupported-burnt"):
        unsupported = prepare("unsupported-burnt", omit="burnt", negative=True)
        with zipfile.ZipFile(unsupported / "mods/unsupported-burnt-fixture-test-only.jar", "w") as jar:
            jar.writestr("META-INF/neoforge.mods.toml", '''modLoader="lowcodefml"
loaderVersion="[1,)"
license="MIT"
[[mods]]
modId="burnt"
version="1.10.5.3"
displayName="Unsupported Burnt version fixture - TEST ONLY"
''')
        run(unsupported, negative="burnt")
    if not passed("protection-without-core"):
        run(prepare("protection-without-core", include_protection=True, include_core=False, negative=True), negative="overgrown_firebreaks")
    report["result"] = "PASS"
    report["all_test_processes_stopped"] = True
    report_path = session / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf8")
    (PROJECT / ".verification/latest-report.txt").write_text(report_path.as_posix(), encoding="utf8")
    print("ALL PASS: " + str(report_path), flush=True)


if __name__ == "__main__":
    main()
