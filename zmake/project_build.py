import os
import shutil
import subprocess
import sys
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


def run_ext_tool(command, context: ZMakeContext):
    p = subprocess.run(command, capture_output=True, text=True)
    if p.stdout != "":
        context.logger.info(p.stdout)
    if p.stderr != "":
        context.logger.error(p.stderr)
    assert p.returncode == 0


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

    # Prepare JS target dir
    (path_build / context.target_dir).mkdir()


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
                context.logger.info(f"Copy asset as is {file}")
                shutil.copy(file, dest / rel_name)
                continue

            if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                image = utils.image_color_compress(image, None)

            image_io.save_auto(image, dest / rel_name, target_type)
        except Exception as e:
            context.logger.exception(f"FAILED, file {file}")
            raise e


@build_handler("Common files, app.js")
def common_files(context: ZMakeContext):
    for fn in LIST_COMMON_FILES:
        p = context.path / fn
        if p.exists():
            context.logger.debug(f"Copy file {fn}")
            shutil.copy(p, context.path / "build" / fn)


@build_handler("Build app.js")
def handle_appjs(context: ZMakeContext):
    if not (context.path / "app.js").is_file():
        shutil.copy(f"{utils.APP_PATH}/data/app.js", context.path / "build/app.js")
        context.logger.info("Use our app.js template, because they don't exist in proj")
        return

    if context.config["esbuild"]:
        command = [format_batch("esbuild")]
        params = context.config['esbuild_params']

        if params != "":
            command.extend(params.split(" "))

        command.extend(["--platform=node",
                        f"--outdir={context.path / 'build'}",
                        "--format=iife",
                        "--log-level=warning",
                        context.path / "app.js"])

        run_ext_tool(command, context)
    else:
        shutil.copy(context.path / "app.js",
                    context.path / "build" / "app.js")


@build_handler("Build page from src/lib")
def handle_src(context: ZMakeContext):
    if not (context.path / "src").is_dir():
        return

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
    fn = context.path / "build" / context.target_dir / "index.js"
    with open(fn, "w", encoding="utf8") as f:
        f.write(out)

    context.logger.info(f"Created build/{context.target_dir}/index.js")


@build_handler("Process exiting pages")
def handle_app(context: ZMakeContext):
    if not (context.path / context.target_dir).is_dir():
        return

    src_dir = context.path / context.target_dir
    out_dir = context.path / 'build' / context.target_dir

    if context.config["esbuild"]:
        command = [format_batch("esbuild")]
        params = context.config['esbuild_params']

        if params != "":
            command.extend(params.split(" "))

        command.extend(["--platform=node",
                        "--log-level=warning",
                        f"--outdir={out_dir}",
                        "--format=iife"])
        command.extend(list(src_dir.rglob("**/*.js")))
        run_ext_tool(command, context)
    else:
        for file in src_dir.rglob("**/*.js"):
            relative_path = str(file)[len(str(src_dir)) + 1:]
            dest_file = out_dir / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(file, dest_file)


@build_handler("Post-processing JS files")
def handle_post_processing(context: ZMakeContext):
    js_dir = context.path / "build" / context.target_dir
    for file in js_dir.rglob("**/*.js"):
        if context.config["with_uglifyjs"]:
            command = [format_batch("uglifyjs")]
            params = context.config['uglifyjs_params']
            if params != "":
                command.extend(params.split(" "))
            command.extend(["-o", str(file), str(file)])
            run_ext_tool(command, context)

        # Inject comment
        with open(file, "r", encoding="utf8") as f:
            content = utils.get_app_asset("comment.js") + "\n" + f.read()
        with open(file, "w", encoding="utf8") as f:
            f.write(content)


@build_handler("Preview")
def zepp_preview(context: ZMakeContext):
    if not context.config["mk_preview"]:
        context.logger.info("Skip, disabled")
        return

    command = [format_batch("zepp-preview"),
               "-o", context.path / "dist",
               "--gif",
               context.path / "build"]

    run_ext_tool(command, context)
    assert (context.path / "dist/preview.png").is_file()
    assert (context.path / "dist/preview.gif").is_file()

    if context.config["add_preview_asset"] and (context.path / "build" / "watchface").is_dir():
        context.logger.info("Add preview.png (128x326) to assets")
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
            if ".DS_Store" in fn or "Thumbs.db" in fn:
                context.logger.info(f"Skip: {fn}")
                continue
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
        context.logger.info("Skip, disabled")
        return

    path = context.config["adb_path"]

    basename = context.path.name
    dist_zip = context.path / "dist" / f"{basename}.zip"

    adb = format_executable("adb")

    try:
        run_ext_tool([adb, "shell", "mkdir", "-p", path], context)
        run_ext_tool([adb, "push", dist_zip, path], context)
        run_ext_tool([adb, "shell", f"cd {path} && unzip -o {basename}.zip"], context)
        run_ext_tool([adb, "shell", "rm", f"{path}/{basename}.zip"], context)
    except AssertionError:
        context.logger.info("ADB install failed, ignore")
