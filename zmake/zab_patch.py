import json
import shutil
import time
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from qrcode import QRCode, ERROR_CORRECT_L

from zmake.utils import APP_PATH

source_to_device = {}
with open(APP_PATH / "data" / "zepp_devices.json", "r") as f:
    for obj in json.load(f):
        for source in obj["deviceSource"]:
            source_to_device[source] = obj['deviceName']


def process(zab_path: Path, server_url: str):
    zab = ZipFile(zab_path, "r")
    mapping_data = {"source_redirect": {}, "device_qr": {}}
    manifest = json.loads(zab.read("manifest.json"))

    # Try to load app.json...
    app_json_path = zab_path.parent.parent / "app.json"
    app_json = {}
    if app_json_path.is_file():
        with app_json_path.open("r") as f:
            app_json = json.loads(f.read())

    # Prepare links/paths
    server_id = zab_path.name.split("-")[0]
    output = zab_path.parent / "serve" / server_id

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    target_type = ""
    for zpk_info in manifest["zpks"]:
        filename = zpk_info["name"]
        zpk_data = zab.read(filename)

        if target_type == "":
            target_type = zpk_info["appType"]
        elif target_type != zpk_info["appType"]:
            raise ValueError("Wtf, mixed app/wf package??")

        if zpk_info["appType"] == "app":
            redirect_url, qr_url = process_app_zpk(zpk_data, output, filename, f"{server_url}/{server_id}")
        else:
            redirect_url, qr_url, wf_json_data = process_wf_zpk(zpk_data, zpk_info, output, filename, f"{server_url}/{server_id}")

        # Identify device
        # if "deviceSource" in zpk_info:
        device_qr, source_maps = get_device_map(zpk_info, redirect_url, qr_url)
        # else:
        # device_qr, source_maps = get_device_map_app_json(app_json, zpk_info, filename, redirect_url, qr_url)
        if zpk_info["appType"] == "watchface":
            wf_json_data["devices"] = list(source_maps.keys())
            with open(output / filename.replace(".zpk", ".json"), "w") as f:
                f.write(json.dumps(wf_json_data))
        mapping_data["source_redirect"].update(source_maps)
        mapping_data["device_qr"].update(device_qr)

        # QR image
        qr = QRCode(error_correction=ERROR_CORRECT_L, box_size=8)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output / filename.replace(".zpk", "_qr.png"))

    with open(output / "map.json", "w") as f:
        f.write(json.dumps(mapping_data))

    zab.close()

    _get_analytics(mapping_data["source_redirect"].keys())

    return output


def _get_analytics(sources):
    print("Device compatibility report:")
    for sid in sources:
        if sid not in source_to_device:
            print(f"- Device not supported by zmake: {sid}, it may be unavailable in bundle")

    count_supported = 0
    unsupported_devices = []
    for sid in source_to_device:
        if sid in sources:
            count_supported += 1
        elif source_to_device[sid] not in unsupported_devices:
            unsupported_devices.append(source_to_device[sid])

    print(f"- Device model coverage: {round(count_supported / len(source_to_device.keys()) * 100)}%")
    if len(unsupported_devices) < 1:
        print("- App bundle supports all known ZeppOS devices")
    else:
        print("- Not supported by app:", ", ".join(unsupported_devices))


def get_device_map_app_json(app_json, zpk_info, filename, redirect_url, qr_url):
    #target = filename.split("-" + zpk_info["platforms"][0]['cpuPlatform'])[0]
    target = list(app_json["targets"].keys())[0]
    return get_device_map(app_json["targets"][target], redirect_url, qr_url)


def get_device_map(zpk_info, redirect_url, qr_url):
    devices = []
    for platform in zpk_info["platforms"]:
        source_id = platform["deviceSource"]
        if source_id not in source_to_device:
            raise ValueError(f"Unsupported deviceSource {source_id}")

        device_id = source_to_device[source_id]
        if device_id not in devices:
            devices.append(device_id)

    # Push device map data
    device_qr = {}
    for device_id in devices:
        if device_id in device_qr:
            continue
        device_qr[device_id] = qr_url

    # Source map
    source_map = {}
    for platform in zpk_info["platforms"]:
        source_id = platform["deviceSource"]
        if source_id in source_map:
            continue
        source_map[source_id] = redirect_url

    return device_qr, source_map


def process_wf_zpk(zpk_data, zpk_info, output: Path, filename: str, download_url: str):
    zpk = ZipFile(BytesIO(zpk_data), "r")

    # Get device BIN file
    wf_bin = zpk.read("device.zip")
    wf_bin_fn = filename.replace(".zpk", ".bin")
    with open(output / wf_bin_fn, "wb") as f:
        f.write(wf_bin)
    zpk.close()

    # Get preview from device.zip (idk why they was required)
    wf_png_fn = filename.replace(".zpk", ".png")
    with ZipFile(BytesIO(wf_bin), "r") as wf_zip:
        bin_manifest = json.loads(wf_zip.read("app.json"))
        preview_data = wf_zip.read("assets/" + bin_manifest["app"]["icon"])
    with open(output / wf_png_fn, "wb") as f:
        f.write(preview_data)

    wf_json_fn = filename.replace(".zpk", ".json")
    redirect_url = download_url + "/" + wf_json_fn
    qr_url = download_url.replace("https:", "watchface:") + "/" + wf_json_fn
    return redirect_url, qr_url, {
        "appid": bin_manifest["app"]["appId"],
        "name": bin_manifest["app"]["appName"],
        "updated_at": round(time.time() / 1000),
        "url": download_url + "/" + wf_bin_fn,
        "preview": download_url + "/" + wf_png_fn,
        "devices": []
    }


def process_app_zpk(zpk_data, output: Path, filename: str, download_url: str):
    # Patch zpk to give ability to delete them after use
    patched_zpk = apply_zpk(BytesIO(zpk_data), [
        patch_prod2preview
    ])
    with open(output / filename, "wb") as f:
        f.write(patched_zpk)

    redirect_url = download_url + "/" + filename
    qr_url = download_url.replace("https:", "zpkd1:") + "/" + filename
    return redirect_url, qr_url


# -----------------------------------------------------------------------------------

def apply_zpk(zpk: BytesIO, patches: list):
    output = BytesIO()
    input_zip = ZipFile(zpk, "r")
    output_zip = ZipFile(output, "w", ZIP_DEFLATED)

    for filename in input_zip.namelist():
        if not filename.endswith(".zip"):
            continue
        part_data = BytesIO(input_zip.read(filename))
        new_data = apply_zip(part_data, patches, filename)
        output_zip.writestr(filename, new_data)

    input_zip.close()
    output_zip.close()

    return output.getvalue()


def apply_zip(zip_data, patches, section="device.zip"):
    output = BytesIO()
    input_zip = ZipFile(zip_data, "r")
    output_zip = ZipFile(output, "w")

    for filename in input_zip.namelist():
        data = input_zip.read(filename)
        for patch in patches:
            data = patch(section, filename, data)
        output_zip.writestr(filename, data)

    input_zip.close()
    output_zip.close()

    return output.getvalue()


# ----------------------------------------------------------


def patch_prod2preview(_, file, file_data):
    if file != "app.json":
        return file_data

    data = json.loads(file_data.decode("utf8"))
    if "packageInfo" in data:
        data["packageInfo"]["mode"] = "preview"
    return json.dumps(data).encode("utf8")
