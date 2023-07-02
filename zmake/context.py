import json
import logging
import os
import random
import shutil
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from zmake import utils, image_io, constants
from zmake.utils import read_json

BUILD_HANDLERS = []


class QuietExitException(Exception):
    pass


def build_handler(name):
    def _w(func):
        BUILD_HANDLERS.append([name, func])
        return func
    return _w


ASK_PROJECT_TYPE = """Select new project type:
w - Watchface
a - Application"""

ASK_CONVERT_DIRECTION = """This dir contains both converted and non-converted images
Tell what do you want:
1 - PNG -> TGA
2 - TGA -> PNG"""


class ZMakeContext:
    def __init__(self, path: Path):
        self.target_dir = ""
        self.zeus_platform_target = ""
        self.path = path
        self.path_assets = path / "assets"
        self.config = {}
        self.app_json = {}
        self.logger = logging.getLogger("zmake")

        self.load_config()

    def load_config(self):
        self.logger.info("Use config files:")
        for file in self.list_config_locations():
            if not file.is_file():
                continue

            self.logger.info(f"  {file}")
            with file.open("r", encoding="utf8") as f:
                overlay = json.loads(f.read())

            for i in overlay:
                self.config[i] = overlay[i]

    def list_config_locations(self):
        return [
            utils.APP_PATH / "zmake.json",
            constants.CONFIG_DIR / "zmake.json",
            self.path / "zmake.json",
        ]

    def ask_question(self, message, options):
        self.logger.info(message)
        result = ""
        while result not in options:
            result = input(f"{options} > ")
        return result

    def perform_auto(self):
        if self.path.name.endswith(".bin") or self.path.name.endswith(".zip"):
            self.logger.info("We think that you want to unpack this file")
            self.process_bin()
        elif self.path.is_dir() and next(self.path.iterdir(), False) is False:
            self.logger.info("We think that you want to create new project in this empty dir")
            self.process_empty()
        elif self.path.is_dir() and (self.path / "app.json").is_file():
            self.logger.info("We think that you want... build this project")
            self.process_project()
        else:
            self.logger.info("We think that you want... convert some images")
            self.process_convert_auto()

    def process_empty(self):
        inp = self.ask_question(ASK_PROJECT_TYPE, ["w", "a"])
        source_dirname = "page" if inp == "a" else "watchface"

        with (self.path / "app.json").open("w", encoding="utf8") as f:
            app_json = json.loads(utils.get_app_asset(f"app_{inp}.json"))
            app_json['app']['appId'] = random.randint(0x0000FFFF, 0x7FFFFFFF)
            app_json['app']['appName'] = self.path.name
            app_json['app']['vender'] = os.getlogin()
            f.write(json.dumps(app_json, indent=2, sort_keys=True))

        for n in ["assets", source_dirname]:
            (self.path / n).mkdir()

        shutil.copy(utils.APP_PATH / "data" / f"template_index_{inp}.js",
                    self.path / source_dirname / "index.js")
        shutil.copy(utils.APP_PATH / "data" / "app.js",
                    self.path / "app.js")

    def process_bin(self):
        dest = Path(str(self.path)[:-4])
        if dest.is_dir():
            raise FileExistsError(f"Folder {dest} already exists")
        dest.mkdir()

        with ZipFile(self.path, "r") as f:
            f.extractall(dest)

        self.path = dest
        self.process_decode_images()

    def process_convert_auto(self):
        files_png = 0
        files_tga = 0

        iterator = self.path.rglob("**/*.png")
        if self.path.is_file():
            iterator = [self.path]

        for file in iterator:
            file_type = image_io.get_format(file)
            if file_type == "N/A":
                continue

            if file_type == "PNG":
                files_png += 1
            elif file_type.startswith("TGA"):
                files_tga += 1

        if files_tga == 0:
            self.logger.info("Direction: PNG -> TGA")
            return self.process_encode_images()
        elif files_png == 0:
            self.logger.info("Direction: TGA -> PNG")
            return self.process_decode_images()

        v = self.ask_question(ASK_CONVERT_DIRECTION, ["1", "2"])

        if v == "1":
            return self.process_encode_images()
        else:
            return self.process_decode_images()

    def get_img_target_type(self, file: Path):
        mode_table = {
            "rgb": "TGA-16",
            "rgba": "TGA-32",
            "p": "TGA-P",
            "rlp": "TGA-RLP"
        }

        mode = self.config["def_format"]
        for a in mode_table:
            if file.name.endswith(f".{a}.png") or f".{a}/" in str(file):
                mode = mode_table[a]
                break

        return mode

    def process_encode_images(self):
        iterator = self.path.rglob("**/*.png")
        if self.path.is_file():
            iterator = [self.path]

        statistics = {}
        for file in iterator:
            try:
                image, file_type = image_io.load_auto(file, self.config["encode_mode"])
                target_type = self.get_img_target_type(file)
                if file_type == target_type or file_type == "N/A":
                    continue

                if self.config["auto_rgba"]:
                    count_colors = len(Counter(image.getdata()).values())
                    if count_colors > 256:
                        target_type = "TGA-32"

                if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                    image = utils.image_color_compress(image, file, self.logger)

                ret = image_io.save_auto(image, file, target_type, self.config["encode_mode"])
                assert ret is True
                utils.increment_or_add(statistics, target_type)
            except Exception as e:
                self.logger.exception(f"FAILED, file {file}")
                raise e

        for key in statistics:
            self.logger.info(f"  {statistics[key]} saved in {key} format")

    def process_decode_images(self):
        iterator = self.path.rglob("**/*.png")
        if self.path.is_file():
            iterator = [self.path]

        for file in iterator:
            try:
                image, file_type = image_io.load_auto(file, self.config["encode_mode"])
                if file_type == "PNG" or file_type == "N/A":
                    continue

                image.save(file)
            except Exception as e:
                self.logger.exception(f"FAILED, file {file}")
                raise e

    def check_override_relative(self, rel_name):
        if rel_name in self.config["overrides"]:
            new_name = self.config["overrides"][rel_name]
            self.logger.info(f"  Override {rel_name} -> {new_name}")
            return new_name
        return rel_name

    def check_override(self, file: Path):
        rel_name = str(file)[len(str(self.path)) + 1:]
        if rel_name.endswith("/"):
            rel_name = rel_name[:-1]

        if rel_name in self.config["overrides"]:
            new_name = self.config["overrides"][rel_name]
            self.logger.info(f"  Override {rel_name} -> {new_name}")
            return self.path / new_name
        return file

    def process_project(self):
        self.app_json = read_json(self.check_override(self.path / "app.json"))

        self.target_dir = "watchface"
        if self.app_json["app"]["appType"] == "app":
            self.target_dir = "page"
        if self.config["target_dir_override"] != "":
            self.target_dir = self.config["target_dir_override"]

        for name, func in BUILD_HANDLERS:
            func(self)

        self.logger.info("Completed without error.")
