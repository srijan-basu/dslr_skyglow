#Read a CR3 file and return the green channel  
import numpy as np
import rawpy

def load_green(path):
    # read raw an extracting required values
    with rawpy.imread(path) as raw:
        img=raw.raw_image_visible.astype(np.float64)
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