#Calculates ZP from magnitude of catalog stars
import numpy as np
from src.photometry_tools import *

#Returns median zp, err and no.of stars used
def zp(img, stars, exp_time, sat_lvl, k=0.25, min_stars=5, snr_min=30, sat_frac=0.7):
    zps=[]
    for s in stars:
        #convert to x and y for binned image
        xb, yb = (s["x_full"]-0.5)/2, (s["y_full"]-0.5)/2

        #adjust to brightest centre
        c = centroid(img, xb, yb)

        #calculate flux
        m = aperture_flux(img, *c) if c else None

        #calculating zp of stars that have usable snr, flux and peak value
        if(m is not None and np.isfinite(m["flux"]) and m["flux"]>0 and m["snr"]>=snr_min and m["peak"]<= sat_lvl*sat_frac):
            zps.append(s["V"]+k*s["airmass"]+ 2.5*np.log10(m["flux"]/exp_time))

    print(f"{len(zps)} of {len(stars)} stars used")

    if len(zps)<min_stars:
        raise RuntimeError(f"Only {len(zps)} usable stars found")

    #Calculate median zp and error value.
    zp_med, scatter, n = clipped_median(zps)
    err = 1.2533*scatter/np.sqrt(n)

    return zp_med, err, n


        
