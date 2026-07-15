from pyfilterbank.splweighting import a_weighting_coeffs_design,c_weighting_coeffs_design
    
    
def design_a_weighting(fs):
    return a_weighting_coeffs_design(fs)

def design_c_weighting(fs):
    return c_weighting_coeffs_design(fs)