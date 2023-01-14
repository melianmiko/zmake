import json
import logging
import os
import shutil
from pathlib import Path
from zipfile import ZipFile

import random
from zmake import utils, image_io

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
        self.path = path
        self.config = json.loads(utils.get_app_asset("config.json"))
        self.app_json = {}
        self.logger = logging.getLogger("zmake")

        if (path / "zmake.json").is_file():
            self.merge_app_config()

    def ask_question(self, message, options):
        self.logger.info(message)
        result = ""
        while result not in options:
            result = input(f"{options} > ")
        return result

    def perform_auto(self):
        if self.path.name.endswith(".bin"):
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

        for file in iterator:
            try:
                image, file_type = image_io.load_auto(file)
                target_type = self.get_img_target_type(file)
                if file_type == target_type or file_type == "N/A":
                    continue

                if target_type in ["TGA-P", "TGA-RLP"] and not image.getcolors():
                    image = utils.image_color_compress(image, file, self.logger)

                image_io.save_auto(image, file, target_type)
            except Exception as e:
                self.logger.exception(f"FAILED, file {file}")
                raise e

    def process_decode_images(self):
        iterator = self.path.rglob("**/*.png")
        if self.path.is_file():
            iterator = [self.path]

        for file in iterator:
            try:
                image, file_type = image_io.load_auto(file)
                if file_type == "PNG" or file_type == "N/A":
                    continue

                image.save(file)
            except Exception as e:
                self.logger.exception(f"FAILED, file {file}")
                raise e

    def merge_app_config(self):
        self.logger.debug("Use config overlay")
        with (self.path / "zmake.json").open("r", encoding="utf8") as f:
            overlay = json.loads(f.read())

        for i in overlay:
            self.config[i] = overlay[i]

    def process_project(self):
        with open(self.path / "app.json", "r", encoding="utf8") as f:
            self.app_json = json.loads(f.read())

        self.target_dir = "watchface"
        if self.app_json["app"]["appType"] == "app":
            self.target_dir = "page"

        for name, func in BUILD_HANDLERS:
            self.logger.info(f"-- Stage: {name}")
            func(self)

        self.logger.info("Completed without error.")
