import numpy as np

def sosfilt_np(sos, x, zi=None):
    """
    sos: (n_sections, 6) [b0,b1,b2,a0,a1,a2]
    x: 1D array
    zi: (n_sections, 2) or None

    returns y, zf
    """
    sos = np.asarray(sos, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)

    nsec = sos.shape[0]
    if zi is None:
        z = np.zeros((nsec, 2), dtype=np.float64)
    else:
        z = np.asarray(zi, dtype=np.float64).copy()

    y = x.copy()

    for s in range(nsec):
        b0, b1, b2, a0, a1, a2 = sos[s]
        if a0 != 1.0:
            b0, b1, b2, a1, a2 = b0/a0, b1/a0, b2/a0, a1/a0, a2/a0

        z1, z2 = z[s, 0], z[s, 1]
        out = np.empty_like(y)

        for n in range(len(y)):
            xn = y[n]
            yn = b0*xn + z1
            z1 = b1*xn - a1*yn + z2
            z2 = b2*xn - a2*yn
            out[n] = yn

        y = out
        z[s, 0], z[s, 1] = z1, z2

    return y, z
