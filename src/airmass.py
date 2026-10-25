#Calculates Airmass
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
from astropy.utils.iers import conf as iers_conf
#bypass iers date check
iers_conf.auto_max_age=None

def airmass_from_altitude(alt_deg):
    
    #Uses Kasten and Yound airmass for altitude upto 5 deg above horizon. Returns nan below that as value is too uncertain
    alt = np.asarray(alt_deg, dtype=float)
    am = 1/(np.sin(np.radians(alt)) + 0.50572*(6.07995+alt)**-1.6364)
    return np.where(alt>5, am, np.nan)

def altitude_of_target(ra, dec, lat, lon, utc_time, height=10.0):
    
    #Returns array of altitudes of target from location, time, height in meters and angle parameters in degrees
    #Can input one set of coords or array of coords for calculating for multiple stars individually.
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=height*u.m)
    obs_time = utc_time if isinstance(utc_time, Time) else Time(utc_time, scale="utc")
    target = SkyCoord(ra=np.atleast_1d(ra)*u.deg, dec=np.atleast_1d(dec)*u.deg, frame="icrs")
    altaz = target.transform_to(AltAz(obstime=obs_time, location=location))
    return altaz.alt.deg


def airmass(ra, dec, lat, lon, utc_time, height=10.0):

    #returns airmass and altitude as arrays, one element per star
    alt = altitude_of_target(ra, dec, lat, lon, utc_time, height)
    return alt, airmass_from_altitude(alt)


if __name__ == "__main__":
    #just for testing
    alt, am = airmass(0, 90, 0.0, 0.0, "2026-10-23T12:20:00")
    print(f"Altitude: {alt[0]:.2f} deg")
    print(f"Airmass:  {am[0]:.3f}")
