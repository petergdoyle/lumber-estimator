import pandas as pd

def parse_fraction(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val = str(val).strip()
    if not val:
        return 0.0
        
    # Handle fractions like "54 1/4" or "1/4"
    parts = val.split()
    total = 0.0
    for part in parts:
        if '/' in part:
            try:
                num, den = part.split('/')
                total += float(num) / float(den)
            except ValueError:
                pass
        else:
            try:
                total += float(part)
            except ValueError:
                pass
    return total

def calculate_bf(length, width, thickness_moniker="4/4"):
    """
    Calculate Board Feet based on rough dimensions
    """
    if '/' in thickness_moniker:
        try:
            num, den = thickness_moniker.split('/')
            nominal_thickness = float(num) / float(den)
        except ValueError:
            nominal_thickness = 1.0
    else:
        try:
            nominal_thickness = float(thickness_moniker)
        except ValueError:
            nominal_thickness = 1.0
        
    bf = (length * width * nominal_thickness) / 144.0
    return bf
    
def calculate_sqft(length, width):
    """
    Calculate Square Feet
    """
    return (length * width) / 144.0
