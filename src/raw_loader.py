#Read a CR3 file and return the green channel  
import numpy as np
import rawpy
from pathlib import Path

#Returns the gren binned image and usable saturation level
def load_green(path):
    # Reading raw file even if input is path object
    path_str = str(path) if isinstance(path, Path) else path
    with rawpy.imread(path_str) as raw:
        img=raw.raw_image_visible.astype(np.float64)
        s=raw.sizes

        #Canon applies a default crop of 6000*4000 for JPEG images used for astrometry.net plate solve.
        #raw_image_visible returns 6024*4020 therefore we need to apply the crop here as well
        dx = s.crop_left_margin-s.left_margin
        dy = s.crop_top_margin-s.top_margin
        if(dx%2!=0 or dy%2!=0):
            raise ValueError(f"Crop offset ({dx}, {dy}) is odd, which would swap the Bayer pattern")
        img = img[dy: dy+s.crop_height, dx: dx+s.crop_width]
        
        pattern=raw.raw_pattern
        black=float(np.mean(raw.black_level_per_channel))
        white=float(raw.white_level)
  
    # subtract black level
    img-=black

    #seperate green channel checks for 2*2 Bayer pattern
    greens=[(r, c) for r in range(2) for c in range(2)
            if pattern[r, c] in (1, 3)]
    if len(greens) != 2:
        raise ValueError(f"Expected 2 green positions, found {len(greens)}. "f"Pattern was:\n{pattern}")

    #split green channels
    (r1, c1), (r2, c2) = greens
    g1 =img[r1::2, c1::2]
    g2 =img[r2::2, c2::2]

    #makes size of both green channel same if odd no. of rows and column present
    h = min(g1.shape[0], g2.shape[0])
    w = min(g1.shape[1], g2.shape[1])
    g1 = g1[:h, :w]
    g2 = g2[:h, :w]

    #returns avg of both and also the white level
    return 0.5 * (g1 + g2), white-black

if __name__ == "__main__":
    import sys
    green, white = load_green(sys.argv[1])
    print("Green image shape:", green.shape)
    print("Median counts:", np.median(green))
    print("White level:", white)