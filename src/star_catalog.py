#Create Reference star list from plate solve data and query for magnitudes to Tycho-2
import numpy as np
from pathlib import Path
from astropy.table import Table
from astropy.wcs import WCS, utils
from astropy.io import fits
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from src.airmass import *

#Calculate star positions on image from axy.fits
def read_axy(path):
    t = Table.read(path)
    cols = {c.upper(): c for c in t.colnames}
    x = np.array(t[cols["X"]], float) - 1.0           
    y = np.array(t[cols["Y"]], float) - 1.0
    flux = np.array(t[cols["FLUX"]], float) if "FLUX" in cols else np.ones_like(x)
    return x, y, flux

#Func to query Tycho catalog using vizier
def fetch_tycho(ra_deg, dec_deg, radius_deg, vt_max, cache_dir):
    #checks stored cache before querying
    cache_dir= Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path=cache_dir/f"tycho2_ra{ra_deg:.3f}_dec{dec_deg:.3f}_r{radius_deg:.3f}_vt{vt_max:g}.ecsv"
    if Path(cache_path).exists():  
        print("Using cached data...")                    
        return Table.read(cache_path, format="ascii.ecsv")

    v = Vizier(
        columns=["TYC1", "TYC2", "TYC3", "RA(ICRS)", "DE(ICRS)", "BTmag", "VTmag"],
        column_filters={"VTmag": f"<{vt_max}"},         
        row_limit=-1,                                    
    )
    v.TIMEOUT = 120
    v.VIZIER_SERVER= "vizier.cfa.harvard.edu"
    res = v.query_region(SkyCoord(ra_deg * u.deg, dec_deg * u.deg), radius=radius_deg * u.deg, catalog="I/259/tyc2")
    if len(res) == 0:
        raise RuntimeError("Vizier returned no Tycho-2 stars.")
    res[0].write(cache_path, format="ascii.ecsv", overwrite=True)
    return res[0]

#Building the star catalog
def build_star_catalog(axy_path, wcs_path, obs_time_utc, site, cache_dir="data/catalog_cache", mag_min=3, mag_max=6, match_px=4.0, 
                       n_brightest=400,min_alt_deg=30.0, crowd_px=16.0):

    #Read wcs.fits   
    with fits.open(wcs_path) as h:
        hdr = h[0].header
        wcs = WCS(hdr, naxis=2)
        img_w, img_h = int(hdr["IMAGEW"]), int(hdr["IMAGEH"])
        scale = float(np.mean(utils.proj_plane_pixel_scales(wcs)) * 3600.0)

    #Read axy.fits
    x, y, flux = read_axy(axy_path)
    top = np.argsort(flux)[::-1][:n_brightest]
    x, y = x[top], y[top]
    src = wcs.pixel_to_world(x, y)

    #Calculates centre and radius for querying tycho catalog at once
    centre = wcs.pixel_to_world((img_w - 1) / 2, (img_h - 1) / 2)
    radius = scale * np.hypot(img_w, img_h) / 2 / 3600 * 1.05

    #Fetching actual ra, dec, vt and bt from catalog
    catalog = fetch_tycho(centre.ra.deg, centre.dec.deg, radius, mag_max, cache_dir)
    if catalog is None or len(catalog) == 0:
        raise ValueError(f"Tycho-2 query returned 0 stars for center RA={centre.ra.deg:.2f}, Dec={centre.dec.deg:.2f} with radius={radius:.2f} deg.")
    cra, cdec = np.array(catalog["RA(ICRS)"], float), np.array(catalog["DE(ICRS)"], float)
    vt = np.array(catalog["VTmag"], float)
    bt = np.array(catalog["BTmag"], float)

    ccoord = SkyCoord(cra * u.deg, cdec * u.deg)
    cx, cy = wcs.world_to_pixel(ccoord)

    #Matchs coords in image to coords from catalog and also finds seperation
    idx, sep, _ = src.match_to_catalog_sky(ccoord)
    sep_px = sep.arcsec / scale
    ok = sep_px < match_px

    #Takes best star in case of two stars pointing to one in catalog
    best = {}
    for d in np.where(ok)[0]:
        c = idx[d]
        if c not in best or sep_px[d] < sep_px[best[c]]:
            best[c] = d

    #Arranging all values into the rows after sorting out crowded stars, stars below alt 30 deg and over or under saturated stars
    rows = []
    alt_all = altitude_of_target(cra, cdec, site["lat"], site["lon"], obs_time_utc)
    for c, d in best.items():
        if not (mag_min <= vt[c] <= mag_max) or not np.isfinite(alt_all[c]) or alt_all[c] < min_alt_deg:
            continue

        dist = np.hypot(cx - cx[c], cy - cy[c])
        dist[c] = 1e9  
        
        if dist.min() < crowd_px:  
            continue
        
        #Calculating Johnson V from Tycho VT and BT
        #Note the x and y value that the function returns is w.r.t the full res image.
        #To use in zp calibration(which is green channel and binned, thus half res) use formule x_bin=(x_full-0.5)/2 and y_bin=(y_full-0.5)/2
        V = vt[c] - 0.090 * (bt[c] - vt[c]) if np.isfinite(bt[c]) else vt[c]
        rows.append((
            f'{catalog["TYC1"][c]}-{catalog["TYC2"][c]}-{catalog["TYC3"][c]}', 
            x[d], y[d], V,
            bt[c] - vt[c], alt_all[c], 
            float(airmass_from_altitude(alt_all[c])), 
            sep_px[d]
        ))

    #column arrangement with data types
    DTYPE = [
    ("tyc", "U16"), 
    ("x_full", float), 
    ("y_full", float), 
    ("V", float), 
    ("bt-vt", float),
    ("alt", float), 
    ("airmass", float), 
    ("sep_px", float)]

    #final output with msg.
    output = np.array(rows, dtype=DTYPE)
    print(f"{len(src)} detections -> {int(ok.sum())} matched -> {len(output)} kept (V {mag_min}-{mag_max}, alt>{min_alt_deg} deg, isolated)")
    return output

