import shutil
import subprocess
from pathlib import Path

import converter


def is_project(path: Path):
    return (path / "app.json").is_file()


def mk_assets(path: Path, def_format: str):
    print("-- Process assets...")
    source = path / "assets"
    dest = path / "build" / "assets"

    dest.mkdir()
    to_convert = []
    for item in source.rglob("**/*"):
        delta = str(item)[len(str(source)) + 1:]
        target = dest / delta
        if item.is_dir():
            target.mkdir()
        elif item.name.endswith(".png"):
            to_convert.append((item, target))
        else:
            print(f"Copy RAW file: {delta}")
            shutil.copy(item, target)

    converter.to_tga(to_convert, def_format)


def mk_js_content(path: Path):
    print("-- Prepare JS base")

    out = ''
    for directory in [path / 'lib', path / 'src']:
        if not directory.is_dir():
            continue

        for file in sorted(directory.rglob("**/*.js")):
            out += f"// source: {file}\n"
            with file.open("r", encoding="utf8") as f:
                out += f.read() + "\n"

    entrypoint = path / 'entrypoint.js'
    if entrypoint.is_file():
        out += f"// source: {entrypoint}\n"
        with entrypoint.open("r") as f:
            out += f.read() + "\n"

    return out


def mk_esbuild(sources: Path, dest_dir: Path, params):
    cmd = ["esbuild"]
    cmd.extend(params.split(" "))
    cmd.extend([f"--outdir={dest_dir}", "--platform=node", "--format=iife"])

    for file in sources.rglob("*.js"):
        cmd.append(str(file))

    print(cmd)
    subprocess.Popen(cmd).wait()


def mk_run_uglify(content: str, params: str):
    print("Run uglifyjs...")
    command = ["uglifyjs"]
    if params != "":
        command.extend(params.split(" "))
    uglify = subprocess.run(command,
                            input=content.encode("utf8"),
                            stdout=subprocess.PIPE)
    assert uglify.returncode == 0
    return uglify.stdout.decode("utf8")


def mk_preview(path: Path):
    print("-- Prepare preview")
    subprocess.Popen(["zepp-preview", "-o", path / "dist",
                      "--gif", path / "build"]).wait()

    assert (path / "dist/preview.png").is_file()
    assert (path / "dist/preview.gif").is_file()
