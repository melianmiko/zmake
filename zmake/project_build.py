import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from zmake import utils, image_io
from zmake.context import build_handler, ZMakeContext

LIST_COMMON_FILES = [
    "app.json",
    "README.txt",
    "LICENSE.txt",
    "README",
    "LICENSE"
]


def format_executable(n):
    if sys.platform == "win32":
        return f"{n}.exe"
    return n


def format_batch(n):
    if sys.platform == "win32":
        return f"{n}.cmd"
    return n


def _js_process(path: Path, dest: Path, context: ZMakeContext, target_dir: str,
                with_banner=True):

    if path.is_file():
        source_paths = [path]
    else:
        source_paths = list(path.rglob("**/*.js"))

    for file in path.rglob("**/*"):
        if file.is_dir():
            rel_name = str(file)[len(str(path)) + 1:]
            os.mkdir(dest / rel_name)

    if context.config["esbuild"]:
        command = [format_batch("esbuild")]
        params = context.config['esbuild_params']

        if params != "":
            command.extend(params.split(" "))

        command.extend(["--platform=node",
                        "--allow-overwrite",
                        f"--outdir={dest}",
                        "--format=iife"])
        command.extend(source_paths)
        p = subprocess.run(command)
        assert p.returncode == 0

        for i in range(len(source_paths)):
            source_paths[i] = dest / source_paths[i].name

    for source in source_paths:
        rel_name = str(source)[str(source).index(f"{target_dir}/") + len(target_dir) + 1:]
        if target_dir == "":
            rel_name = source.name

        if context.config["with_uglifyjs"]:
            command = [format_batch("uglifyjs")]
            params = context.config['uglifyjs_params']

            if params != "":
                command.extend(params.split(" "))

            command.extend(["-o", dest / rel_name, source])
            p = subprocess.run(command)
            assert p.returncode == 0

        if with_banner:
            with open(source, "r") as f:
                content = utils.get_app_asset("comment.js") + "\n" + f.read()
            with open(dest / rel_name, "w") as f:
                f.write(content)
        else:
            shutil.copy(source, dest / rel_name)


@build_handler("Prepare")
def prepare(context: ZMakeContext):
    path_build = context.path / "build"
    path_dist = context.path / "dist"

    if path_build.exists():
        shutil.rmtree(path_build)
    if path_dist.exists():
        shutil.rmtree(path_dist)

    path_build.mkdir()
    path_dist.mkdir()


@build_handler("Convert assets")
def handle_assets(context: ZMakeContext):
    source = context.path / "assets"
    dest = context.path / "build" / "assets"
    dest.mkdir()

    for file in source.rglob("**/*"):
        rel_name = str(file)[len(str(source)) + 1:]

        if file.is_dir():
            os.mkdir(dest / rel_name)
            continue

        try:
            image, file_type = image_io.load_auto(file)
            target_type = context.get_img_target_type(file)
            if file_type == target_type or file_type == "N/A":
                print("Copy asset as is", file)
                shutil.copy(file, dest / rel_name)
                continue

            if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                image = utils.image_color_compress(image, None)

            image_io.save_auto(image, dest / rel_name, target_type)
        except Exception as e:
            print(f"FAILED, file {file}")
            raise e


@build_handler("Common files, app.js")
def common_files(context: ZMakeContext):
    for fn in LIST_COMMON_FILES:
        p = context.path / fn
        if p.exists():
            print("Copy file", fn)
            shutil.copy(p, context.path / "build" / fn)

    # Use our app.js
    if not (context.path / "app.js").is_file():
        shutil.copy(f"{utils.APP_PATH}/data/app.js", context.path / "build/app.js")
        return

    # Use user-defined app.js
    _js_process(context.path / "app.js",
                context.path / "build",
                context,
                "")


@build_handler("Make pages/watchface")
def handle_app(context: ZMakeContext):
    with open(context.path / "app.json", "r", encoding="utf8") as f:
        app_config = json.loads(f.read())

    target_dir = "watchface"
    if app_config["app"]["appType"] == "app":
        target_dir = "page"

    os.mkdir(context.path / "build" / target_dir)

    if (context.path / target_dir).is_dir():
        _js_process(context.path / target_dir,
                    context.path / "build" / target_dir,
                    context,
                    target_dir)

    if (context.path / "src").is_dir():
        out = ""
        for directory in [context.path / 'lib', context.path / 'src']:
            if not directory.is_dir():
                continue

            for file in sorted(directory.rglob("**/*.js")):
                out += f"// source: {file}\n"
                with file.open("r", encoding="utf8") as f:
                    out += f.read() + "\n"

        entrypoint = context.path / 'entrypoint.js'
        if entrypoint.is_file():
            out += f"// source: {entrypoint}\n"
            with entrypoint.open("r", encoding="utf8") as f:
                out += f.read() + "\n"

        out = utils.get_app_asset("basement.js").replace("{content}", out)
        fn = context.path / "build" / target_dir / "index.js"
        with open(fn, "w", encoding="utf8") as f:
            f.write(out)

        _js_process(fn,
                    context.path / "build" / target_dir,
                    context,
                    target_dir)


@build_handler("Preview")
def zepp_preview(context: ZMakeContext):
    if not context.config["mk_preview"]:
        print("Skip, disabled")
        return

    subprocess.Popen([format_batch("zepp-preview"),
                      "-o", context.path / "dist",
                      "--gif",
                      context.path / "build"]).wait()

    assert (context.path / "dist/preview.png").is_file()
    assert (context.path / "dist/preview.gif").is_file()

    if context.config["add_preview_asset"] and (context.path / "build" / "watchface").is_dir():
        print("Add preview.png (128x326) to assets")
        pv = Image.open(context.path / "dist/preview.png")
        pv.thumbnail((128, 326))
        pv = pv.convert("RGB").quantize(256)
        image_io.save_auto(pv, context.path / "build/assets/preview.png", "TGA-RLP")


@build_handler("Package BIN and ZIP")
def package(context: ZMakeContext):
    basename = context.path.name
    dist_bin = context.path / "dist" / f"{basename}.bin"
    with ZipFile(dist_bin, "w", ZIP_DEFLATED) as arc:
        for file in (context.path / "build").rglob("**/*"):
            fn = str(file)[len(str(context.path / "build")):]
            arc.write(file, fn)

    # ZIP
    dist_infos = context.path / "dist/infos.xml"
    with dist_infos.open("w") as f:
        f.write(utils.get_app_asset("infos.xml").replace("{name}", basename))

    dist_zip = context.path / "dist" / f"{basename}.zip"
    with ZipFile(dist_zip, "w", ZIP_DEFLATED) as arc:
        arc.write(dist_bin, f"{basename}/{basename}.bin")
        arc.write(dist_infos, f"{basename}/infos.xml")
        if (context.path / "dist/preview.png").is_file():
            arc.write(context.path / "dist/preview.png", f"{basename}/{basename}.png")


@build_handler("ADB Install")
def adb_install(context: ZMakeContext):
    if not context.config["adb_install"]:
        print("Skip, disabled")
        return

    path = context.config["adb_path"]

    basename = context.path.name
    dist_zip = context.path / "dist" / f"{basename}.zip"

    adb = format_executable("adb")
    subprocess.Popen([adb, "shell", "mkdir", "-p", path]).wait()
    subprocess.Popen([adb, "push", dist_zip, path]).wait()
    subprocess.Popen([adb, "shell", f"cd {path} && unzip -o {basename}.zip"]).wait()
    subprocess.Popen([adb, "shell", "rm", f"{path}/{basename}.zip"]).wait()
