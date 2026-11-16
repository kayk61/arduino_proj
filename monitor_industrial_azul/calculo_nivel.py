def calculate_level(top,bottom,water,total_height_cm):
    if None in (top,bottom,water) or bottom<=top or total_height_cm<=0: return None,None
    pct=max(0.0,min(100.0,(bottom-water)/(bottom-top)*100.0))
    return total_height_cm*pct/100.0,pct
