#Different aperture and alignment tools to be used in other modules
import numpy as np

#Ring of Pixels between r_in and r_out centred around x and y
def ring(img, x, y, r_in, r_out):
    x0, x1 = int(np.floor(x - r_out))-1, int(np.ceil(x + r_out))+2
    y0, y1 = int(np.floor(y - r_out))-1, int(np.ceil(y + r_out))+2
    if x0<0 or y0<0 or x1>img.shape[1] or y1>img.shape[0]:
        return None
    
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xx - x, yy - y)
    return img[y0:y1, x0:x1][(d>=r_in) & (d<r_out)]

#Removes outliers using robust stdev iteratively and calculates median; also returns robust stdev and no. of values kept
def clipped_median(v, sigma=3.0, iters=5):
    v = np.asarray(v, float).ravel()
    v = v[np.isfinite(v)]
    for _ in range(iters):
        med = np.median(v)
        std = 1.4826 * np.median(np.abs(v - med))
        if std == 0:
            break
        keep = np.abs(v - med) < sigma * std
        if keep.all():
            break
        v = v[keep]

    med = float(np.median(v))
    return med, float(1.4826 * np.median(np.abs(v - med))), int(v.size)

#Shift x y so that it is directly on the brightness weighted centre of the star
def centroid(img, x, y, r=3.0, r_in=5.0, r_out=8.0, max_shift=2.5):
    x0, y0 = x, y
    for _ in range(4):
        bg = ring(img, x, y, r_in, r_out)
        if bg is None or bg.size < 20:
            return None
        sky = clipped_median(bg)[0]

        #creates bounding box around star
        a, b = int(np.floor(x - r)) - 1, int(np.floor(y - r)) - 1
        c, d = int(np.ceil(x + r)) + 2, int(np.ceil(y + r)) + 2
        if a < 0 or b < 0 or c > img.shape[1] or d > img.shape[0]:
            return None
        yy, xx = np.mgrid[b:d, a:c]

        #weight = |star flux-sky brightness|
        w = np.clip(img[b:d, a:c] - sky, 0, None)
        w[np.hypot(xx - x, yy - y) > r] = 0
        if w.sum() <= 0:
            return None
        #shifts to brightness weighted centre
        x, y = float((w * xx).sum() / w.sum()), float((w * yy).sum() / w.sum())

    return (x, y) if np.hypot(x - x0, y - y0) <= max_shift else None

#Calculates star flux, snr and peak value.
#Snr here does not account for the gain and read noise of the camera
def aperture_flux(img, x, y, r_ap=3.0, r_in=5.0, r_out=8.0):
    ap, bg = ring(img, x, y, 0.0, r_ap), ring(img, x, y, r_in, r_out)
    if ap is None or bg is None or bg.size < 20:
        return None
    sky, stdev, n = clipped_median(bg)

    #flux= sum of star pixels - sum of sky pixels
    net = float(ap.sum() - sky * ap.size)
    noise = stdev * np.sqrt(ap.size * (1 + ap.size / n))
    return dict(flux=4.0 * net, sky=sky, snr=net / noise if noise > 0 else 0.0, peak=float(ap.max() - sky))