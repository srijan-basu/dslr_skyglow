#Calibrates lights with darks flats and flat darks
import numpy as np
from raw_loader import load_green

#Creates master from the median or mean of green channels of frames
def make_master(paths, method="median"):
    if not paths:
        raise ValueError("No frames given to make_master")

    #Making array of individual green channels
    greens=[] 
    for p in paths:
        g, _=load_green(str(p))
        greens.append(g.astype(np.float32))

    stack=np.stack(greens, axis=0)
    if method=="median":
        master = np.median(stack, axis=0)
    elif method=="mean":
        master = np.mean(stack, axis=0)
    else:
        raise ValueError("method must be mean or median")

    return  master.astype(np.float32)

#Creates master flat from median(flat)-median(flat dark) and normalized to 1
def make_master_flat(flat_paths, flat_dark_paths):
    flat = make_master(flat_paths)
    flat_dark = make_master(flat_dark_paths)

    master = flat - flat_dark
    norm = np.mean(master)
    if norm <=0:
        raise ValueError("Master flat has non-positive mean value")
    return(master/norm).astype(np.float32)

#Return final calibrated file
def calibrate(light_path, master_dark, master_flat):
    light, _ =load_green(light_path)
    light=light.astype(np.float32)

    if light.shape != master_dark.shape or light.shape != master_flat.shape:
        raise ValueError(f"Shape mismatch: light {light.shape}, dark {master_dark.shape}, flat {master_flat.shape}")

    #To avoid dividing by near zero in dead or vignetted-to-zero pixels
    #Use nanmedian while calculating median later on to ignore nans
    flat_safe = np.where(master_flat > 0.05, master_flat, np.nan)
    calibrated = (light - master_dark) / flat_safe
    return calibrated



