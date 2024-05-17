import io
import json
import os
import shutil
import subprocess
import time
from collections import Counter
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from zmake import utils, image_io, constants
from zmake.context import build_handler, ZMakeContext
from zmake.third_tools_manager import run_ext_tool


def should_ignore_file(filename: str, context: ZMakeContext):
    for file_to_ignore in context.config.get("ignore_files", [".DS_Store", "Thumbs.db"]):
        if file_to_ignore in filename:
            return True

    return False


@build_handler("Pre-build command")
def post_build(context: ZMakeContext):
    if context.config.get("pre_build_script", "") == "":
        return

    subprocess.Popen([os.path.expanduser(context.config["pre_build_script"]), str(context.path)]).wait()


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

    with open(path_build / ".gitignore", "w") as f:
        f.write("*\n")
    with open(path_dist / ".gitignore", "w") as f:
        f.write("*\n")

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
        if target_id not in context.app_json["targets"]:
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
        file = context.check_override(file)

        if file.is_dir():
            os.mkdir(dest / rel_name)
            continue

        try:
            image, file_type = image_io.load_auto(file, context.config["encode_mode"])
            target_type = context.get_img_target_type(file)
            if file_type == target_type or file_type == "N/A":
                context.logger.info(f"Copy asset as is {file}")
                shutil.copy(file, dest / rel_name)
                utils.increment_or_add(statistics, "RAW")
                continue

            if context.config["auto_rgba"]:
                count_colors = len(Counter(image.getdata()).values())
                if count_colors > 256:
                    target_type = "TGA-32"

            if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                image = utils.image_color_compress(image, None, context.logger)

            ret = image_io.save_auto(image, dest / rel_name, target_type, context.config["encode_mode"])
            assert ret is True
            utils.increment_or_add(statistics, target_type)
        except Exception as e:
            context.logger.exception(f"FAILED, file {file}")
            raise e

    if context.config["with_zeus_compat"] and (context.path / "assets" / "raw").is_dir():
        context.logger.info("  Copy RAW files (zeus_compat)")
        shutil.copytree(context.path / "assets" / "raw", dest / "raw")

    for key in statistics:
        context.logger.info(f"  {statistics[key]} saved in {key} format")


@build_handler("Common files")
def common_files(context: ZMakeContext):
    context.logger.info("Copying common files:")
    files = context.config["common_files"]
    for fn in files:
        p = context.path / fn
        if p.is_dir():
            context.logger.info(f"  Copy folder {fn}")
            shutil.copytree(p, context.path / "build" / fn)
        elif p.is_file():
            context.logger.info(f"  Copy file {fn}")
            shutil.copy(p, context.path / "build" / fn)
    context.logger.info("  Done")


@build_handler("Build app.js")
def handle_appjs(context: ZMakeContext):
    context.logger.info("Processing app.js:")

    app_js = context.check_override(context.path / "app.js")
    if not app_js.is_file():
        shutil.copy(f"{utils.APP_PATH}/data/app.js", context.path / "build/app.js")
        context.logger.info("  Use our app.js template")
        return

    if context.config["esbuild"]:
        command = ["esbuild"]
        if context.config["with_zeus_compat"]:
            context.logger.info("  Add zeus_fixes_inject.js")
            command.append(f"--inject:{utils.APP_PATH / 'data' / 'zeus_fixes_inject.js'}")

        command.extend(["--platform=node",
                        f"--outdir={context.path / 'build'}",
                        "--format=iife",
                        "--log-level=warning"])

        params = context.config['esbuild_params']
        if params != "":
            command.extend(params.split(" "))

        command.append(app_js)
        run_ext_tool(command, context, "ESBuild")

        if app_js != (context.path / "app.js"):
            shutil.move(context.path / "build" / app_js.name, context.path / "build" / "app.js")
    else:
        shutil.copy(app_js, context.path / "build" / "app.js")

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


@build_handler("Process JS files")
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

        if context.config["with_zeus_compat"]:
            context.logger.info("Add zeus_fixes_inject")
            command.append(f"--inject:{utils.APP_PATH / 'data' / 'zeus_fixes_inject.js'}")

        command.extend(["--platform=node",
                        "--log-level=warning",
                        f"--outdir={out_dir}",
                        "--format=iife"])

        for file in src_dir.rglob("**/*.js"):
            command.append(context.check_override(file))

        run_ext_tool(command, context, "ESBuild")
        context.logger.info("  ESBuild finished successfully")
    else:
        i = 0
        for file in src_dir.rglob("**/*.js"):
            relative_path = str(file)[len(str(src_dir)) + 1:]
            dest_file = out_dir / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(context.check_override(file), dest_file)
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
        image_io.save_auto(pv, context.path / "build/assets/preview.png", "TGA-RLP", context.config["encode_mode"])

    context.logger.info("  Done")


@build_handler("Package BIN and ZIP")
def package(context: ZMakeContext):
    context.logger.info("Packaging:")
    basename = context.path.name

    device_extension = context.config["package_extension"]
    device_zip = context.path / "dist" / f"{basename}.{device_extension}"
    with ZipFile(device_zip, "w", ZIP_DEFLATED) as arc:
        for file in (context.path / "build").rglob("**/*"):
            fn = str(file)[len(str(context.path / "build")):]
            if should_ignore_file(fn, context):
                context.logger.info(f"Skip: {fn}")
                continue
            arc.write(file, fn)

    # ZIP
    if device_extension != "zip":
        dist_infos = context.path / "dist/infos.xml"
        with dist_infos.open("w") as f:
            f.write(utils.get_app_asset("infos.xml").replace("{name}", basename))

        dist_zip = context.path / "dist" / f"{basename}.zip"
        with ZipFile(dist_zip, "w", ZIP_DEFLATED) as arc:
            arc.write(device_zip, f"{basename}/{basename}.bin")
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
            if should_ignore_file(fn, context):
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


@build_handler("Post-build command")
def post_build(context: ZMakeContext):
    if context.config["post_build_script"] == "":
        return

    subprocess.Popen([os.path.expanduser(context.config["post_build_script"]), str(context.path)]).wait()
