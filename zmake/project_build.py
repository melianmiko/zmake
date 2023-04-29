import io
import json
import os
import shutil
import time
from collections import Counter
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from zmake import utils, image_io, constants
from zmake.context import build_handler, ZMakeContext
from zmake.third_tools_manager import run_ext_tool

LIST_COMMON_FILES = [
    "README.txt",
    "LICENSE.txt",
    "README",
    "LICENSE"
]


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


@build_handler("Process app.json")
def process_app_json(context: ZMakeContext):
    context.logger.info("Processing app.json:")
    package_info = {
        "mode": "preview",
        "timeStamp": round(time.time()),
        "expiredTime": 157680000,
        "zpm": "2.6.6",
        "zmake": constants.VERSION
    }

    context.app_json["packageInfo"] = package_info
    context.app_json["platforms"] = context.config["zeus_platforms"]

    if "targets" in context.app_json:
        target_id = context.config["zeus_target"]
        if target_id not in context.app_json:
            target_id = list(context.app_json["targets"].keys())[0]
        context.logger.info(f"  Found targets, use \"{target_id}\" target")

        context.path_assets = context.path / "assets" / target_id

        for key in context.app_json["targets"][target_id]:
            context.app_json[key] = context.app_json["targets"][target_id][key]

        del context.app_json["targets"]

    app_json_string = json.dumps(context.app_json, indent=4, sort_keys=True)
    with open(context.path / "build" / "app.json", "w") as f:
        f.write(app_json_string)

    context.logger.info("  Done")


@build_handler("Convert assets")
def handle_assets(context: ZMakeContext):
    source = context.path_assets
    dest = context.path / "build" / "assets"
    dest.mkdir()

    context.logger.info("Processing assets:")

    statistics = {}
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
                utils.increment_or_add(statistics, "RAW")
                continue

            if context.config["auto_rgba"]:
                count_colors = len(Counter(image.getdata()).values())
                if count_colors > 256:
                    target_type = "TGA-RGBA"

            if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                image = utils.image_color_compress(image, None, context.logger)

            image_io.save_auto(image, dest / rel_name, target_type)
            utils.increment_or_add(statistics, target_type)
        except Exception as e:
            context.logger.exception(f"FAILED, file {file}")
            raise e

    for key in statistics:
        context.logger.info(f"  {statistics[key]} saved in {key} format")


@build_handler("Common files")
def common_files(context: ZMakeContext):
    context.logger.info("Copying common files:")
    for fn in LIST_COMMON_FILES:
        p = context.path / fn
        if p.exists():
            context.logger.debug(f"Copy file {fn}")
            shutil.copy(p, context.path / "build" / fn)
            context.logger.info(f"Add {fn}")
    context.logger.info("  Done")


@build_handler("Build app.js")
def handle_appjs(context: ZMakeContext):
    context.logger.info("Processing app.js:")
    if not (context.path / "app.js").is_file():
        shutil.copy(f"{utils.APP_PATH}/data/app.js", context.path / "build/app.js")
        context.logger.info("  Use our app.js template")
        return

    if context.config["esbuild"]:
        command = ["esbuild"]
        params = context.config['esbuild_params']

        if params != "":
            command.extend(params.split(" "))

        if context.config["with_zeus_compat"]:
            context.logger.info("  Add zeus_fixes_inject.js")
            command.append(f"--inject:{utils.APP_PATH / 'data' / 'zeus_fixes_inject.js'}")

        command.extend(["--platform=node",
                        f"--outdir={context.path / 'build'}",
                        "--format=iife",
                        "--log-level=warning",
                        context.path / "app.js"])

        run_ext_tool(command, context, "ESBuild")
    else:
        shutil.copy(context.path / "app.js",
                    context.path / "build" / "app.js")

    context.logger.info("Done")


@build_handler("Build page from src/lib")
def handle_src(context: ZMakeContext):
    if not (context.path / "src").is_dir() or (context.path / context.target_dir / "index.js").is_file():
        return

    context.logger.info("Combine src/lib files to index.js:")
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

    context.logger.info(f"  Done")


@build_handler("Process exiting pages")
def handle_app(context: ZMakeContext):
    if not (context.path / context.target_dir).is_dir():
        return

    context.logger.info(f"Processing \"{context.target_dir}\" JS files:")
    src_dir = context.path / context.target_dir
    out_dir = context.path / 'build' / context.target_dir

    if context.config["esbuild"]:
        command = ["esbuild"]
        params = context.config['esbuild_params']

        if params != "":
            command.extend(params.split(" "))

        if context.config["with_zeus_overrides"]:
            context.logger.info("Add zeus_fixes_inject")
            command.append(f"--inject:{utils.APP_PATH / 'data' / 'zeus_fixes_inject.js'}")

        command.extend(["--platform=node",
                        "--log-level=warning",
                        f"--outdir={out_dir}",
                        "--format=iife"])
        command.extend(list(src_dir.rglob("**/*.js")))
        run_ext_tool(command, context, "ESBuild")
        context.logger.info("  ESBuild finished successfully")
    else:
        i = 0
        for file in src_dir.rglob("**/*.js"):
            relative_path = str(file)[len(str(src_dir)) + 1:]
            dest_file = out_dir / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(file, dest_file)
            i += 1
        context.logger.info(f"  Copied {i} files")


@build_handler("Post-processing JS files")
def handle_post_processing(context: ZMakeContext):
    i = 0
    js_dir = context.path / "build" / context.target_dir
    for file in js_dir.rglob("**/*.js"):
        if context.config["with_uglifyjs"]:
            command = ["uglifyjs"]
            params = context.config['uglifyjs_params']
            if params != "":
                command.extend(params.split(" "))
            command.extend(["-o", str(file), str(file)])
            run_ext_tool(command, context, "UglifyJS")

        # Inject comment
        with open(file, "r", encoding="utf8") as f:
            content = utils.get_app_asset("comment.js") + "\n" + f.read()
        with open(file, "w", encoding="utf8") as f:
            f.write(content)
        i += 1

    context.logger.info(f"  Post-processed {i} files")


@build_handler("Preview")
def zepp_preview(context: ZMakeContext):
    if not context.config["with_zepp_preview"]:
        return

    command = ["zepp-preview",
               "-o", context.path / "dist",
               "--gif",
               context.path / "build"]

    context.logger.info("Creating 'preview.png':")

    run_ext_tool(command, context, "ZeppPreview")
    assert (context.path / "dist/preview.png").is_file()
    assert (context.path / "dist/preview.gif").is_file()

    if context.config["add_preview_asset"] and (context.path / "build" / "watchface").is_dir():
        context.logger.info("  Add preview.png (128x326) to assets")
        pv = Image.open(context.path / "dist/preview.png")
        pv.thumbnail((128, 326))
        pv = pv.convert("RGB").quantize(256)
        image_io.save_auto(pv, context.path / "build/assets/preview.png", "TGA-RLP")

    context.logger.info("  Done")


@build_handler("Package BIN and ZIP")
def package(context: ZMakeContext):
    context.logger.info("Packaging:")
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

    context.logger.info("  Created BIN/ZIP files")


@build_handler("Make ZEUS package")
def make_zeus_pkg(context: ZMakeContext):
    if not context.config["with_zeus_compat"]:
        return
    basename = context.path.name

    # Device package
    device_zip_file = io.BytesIO()
    with ZipFile(device_zip_file, "w", ZIP_DEFLATED) as archive:
        for file in (context.path / "build").rglob("**/*"):
            fn = str(file)[len(str(context.path / "build")):]
            if ".DS_Store" in fn or "Thumbs.db" in fn:
                continue
            archive.write(file, fn)

    # App-side package
    app_side_zip_file = io.BytesIO()
    with ZipFile(app_side_zip_file, "w", ZIP_DEFLATED) as archive:
        archive.write(context.path / "build" / "app.json", "app.json")

    # Output
    with ZipFile(context.path / "dist" / f"{basename}.zpk", "w", ZIP_DEFLATED) as arc:
        arc.writestr("device.zip", device_zip_file.getvalue())
        arc.writestr("app-side.zip", app_side_zip_file.getvalue())

    context.logger.info("  Created ZPK file")


@build_handler("ADB Install")
def adb_install(context: ZMakeContext):
    if not context.config["with_adb"]:
        return

    context.logger.info("Uploading to phone via ADB:")
    path = context.config["adb_path"]

    basename = context.path.name
    dist_zip = context.path / "dist" / f"{basename}.zip"

    try:
        run_ext_tool(["adb", "shell", "mkdir", "-p", path], context, "ADB")
        run_ext_tool(["adb", "push", dist_zip, path], context, "ADB")
        run_ext_tool(["adb", "shell", f"cd {path} && unzip -o {basename}.zip"], context, "ADB")
        run_ext_tool(['adb', "shell", "rm", f"{path}/{basename}.zip"], context, "ADB")
    except AssertionError:
        context.logger.info("  Failed, ignore")

    context.logger.info("  ")