import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile


repo = Path(__file__).resolve().parents[2]
fixture = Path(__file__).resolve().parent
work = repo / ".encryption-check"
work.mkdir(exist_ok=True)
platform = "macos.universal" if sys.platform == "darwin" else "linux.x86_64"
archive = work / "godot.zip"
urllib.request.urlretrieve(
    f"https://github.com/godotengine/godot/releases/download/4.5-stable/Godot_v4.5-stable_{platform}.zip",
    archive,
)
with zipfile.ZipFile(archive) as package:
    package.extractall(work)
if sys.platform == "darwin":
    godot = work / "Godot.app/Contents/MacOS/Godot"
    godot.chmod(0o755)
    subprocess.run(["codesign", "--force", "--sign", "-", str(godot)], check=True)
    loader = repo / "target/release/libgdpatch_loader.dylib"
    injection = "DYLD_INSERT_LIBRARIES"
else:
    godot = work / "Godot_v4.5-stable_linux.x86_64"
    godot.chmod(0o755)
    loader = repo / "target/release/libgdpatch_loader.so"
    injection = "LD_PRELOAD"

project = work / "project"
project.mkdir(exist_ok=True)
(project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Pack check"\n')
for name in ["make_pack.gd", "main.gd"]:
    shutil.copyfile(fixture / name, project / name)
(project / "untouched.txt").write_text("x" * 32768)
(project / "untouched.gd").write_text("extends RefCounted\nfunc value():\n    return 37\n")
root = work / "GDPatch"
mod = root / "mods/check"
mod.mkdir(parents=True, exist_ok=True)
(root / "config.toml").write_text('[log]\nconsole=false\n[engine]\nencryption_key="' + "0" * 64 + '"\n')
(mod / "gdpatch_mod.toml").write_text('id="check"\n[meta]\nname="Pack check"\nversion="1.0.0"\n')
(mod / "patcher.lua").write_text('''GDPatch.patch_script_as_text("main.gd", function(_, source)
  local patched, count = source:gsub('"original"', '"patched"', 1)
  assert(count == 1, "script did not match")
  return patched
end)
''')


def run(name, arguments, env=None):
    result = subprocess.run(
        [str(godot), "--headless", *arguments],
        cwd=work, env=env, capture_output=True, text=True, timeout=90,
    )
    output = result.stdout + result.stderr
    (work / (name + ".log")).write_text(output)
    print(output, flush=True)
    result.check_returncode()
    return output


for mode in ["plain", "files", "encrypted"]:
    pack = work / (mode + ".pck")
    run("make-" + mode, ["--path", str(project), "--script", "make_pack.gd", "--", str(pack), mode])
    env = os.environ.copy()
    env[injection] = str(loader)
    env["GDPATCH_ROOT_DIRECTORY"] = str(root)
    output = run(mode, ["--main-pack", str(pack), "--script", "res://main.gd", "--quit-after", "120", "--", str(pack), mode], env)
    if "PACK_CHECK_OK: " + mode not in output:
        raise RuntimeError("pack check did not finish: " + mode)
