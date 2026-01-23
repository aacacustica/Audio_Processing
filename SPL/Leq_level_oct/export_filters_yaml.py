import numpy as np
import yaml
from scipy import signal
from pyfilterbank.splweighting import a_weighting_coeffs_design, c_weighting_coeffs_design



def get_edge_frequencies_1_3(idx_low=-16, idx_high=12):
    # ANSI 1/3 octave band edge frequencies
    G = 10 ** (3 / 10)
    fr = 1000
    b = 3
    idx = np.arange(idx_low, idx_high + 1)
    fm = G ** (idx / b) * fr
    f_upper = fm * G ** (1 / (2 * b))
    f_lower = fm * G ** (-1 / (2 * b))
    return f_lower, fm, f_upper



def export_weighting(fs, out_path):
    bA, aA = a_weighting_coeffs_design(fs)
    bC, aC = c_weighting_coeffs_design(fs)

    data = {
        "fs": int(fs),
        "A_weighting": {"b": np.asarray(bA).tolist(), "a": np.asarray(aA).tolist()},
        "C_weighting": {"b": np.asarray(bC).tolist(), "a": np.asarray(aC).tolist()},
    }
    with open(out_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print("Saved:", out_path)



def export_sos_bank_1_3(fs, order=4, idx_low=-16, idx_high=12, out_path="sos_bank.yaml"):
    f_lower, fm, f_upper = get_edge_frequencies_1_3(idx_low, idx_high)
    nyq = fs / 2.0
    valid = f_upper <= nyq
    f_lower = f_lower[valid]
    f_upper = f_upper[valid]
    
    
    fm = fm[valid]
    sos_bank = []
    for lo, hi in zip(f_lower, f_upper):
        wn = np.array([lo, hi]) / nyq
        sos = signal.butter(order, wn, btype="bandpass", output="sos")
        sos_bank.append(sos.tolist())

    
    
    data = {
        "fs": int(fs),
        "bank": "1/3-octave",
        "order": int(order),
        "idx_low": int(idx_low),
        "idx_high": int(idx_high),
        "freq_center": fm.tolist(),
        "freq_lower": f_lower.tolist(),
        "freq_upper": f_upper.tolist(),
        "sos_bank": sos_bank,
    }

    with open(out_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print("Saved:", out_path, "| bands:", len(fm))





if __name__ == "__main__":
    fs = 32000
    # fs = 16000
    export_weighting(fs, out_path=f"weighting_fs{fs}.yaml")
    export_sos_bank_1_3(fs, order=4, idx_low=-16, idx_high=12,out_path=f"sos_bank_1_3_fs{fs}.yaml")
