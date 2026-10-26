import json
import pathlib as Path
from src.raw_loader import load_green
from src.calibration import calibrate, make_master, make_master_flat

ROOT = Path(__file__).resolve().parent

#Load the config file
def load_config():
    path = ROOT / "config.json"
    if not path.exists():
        print(f"Copy the config.example.json to config.json and change the parameters to fit your sepcifications")
    with open(path) as f:
        return json.load(f)

#fetch files
def get_files(folder, pattern="*.CR3"):
    files = sorted(Path(folder).glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} in {folder}")
    return files


def main():
    cfg = load_config()
    data_dir = ROOT / cfg["data_dir"]

    #Load raw frames (green channel)
    lights = get_files(data_dir/"lights")
    darks  = get_files(data_dir/"darks")
    flats  = get_files(data_dir/"flats")
    flat_darks = get_files(data_dir/"flat_darks")
    print(f"Found {len(lights)} lights, {len(darks)} darks, {len(flats)} flats, {len(flat_darks)} flat darks")

    master_dark=make_master(darks)
    master_flat_dark=make_master(flat_darks)
    master_flat=make_master(flats) - master_flat_dark


    #Process the frames.
    for p in lights:
        light_calibrated= calibrate(p, master_dark, master_flat)
        #TODO: zp calibration and final mag prints

if __name__ == "__main__":
    main()

