from rectpack import newPacker, PackingMode, PackingBin, SORT_AREA

def pack_material(parts, bins, kerf=0.125):
    """
    Executes a 2D bin packing algorithm without rotation (grain alignment enforced).
    
    parts: list of dicts {'id': str, 'desc': str, 'width': float, 'length': float, 'qty': int}
    bins: list of dicts {'id': str, 'label': str, 'width': float, 'length': float, 'qty': int}
    """
    # Integer multiplication maintains perfect precision in rectpack (ignoring weird float limits)
    SCALE = 1000
    
    # We strictly enforce rotation=False for solid wood to preserve grain direction
    packer = newPacker(mode=PackingMode.Offline, bin_algo=PackingBin.BFF, rotation=False)
    
    # Add Bins (Inventory)
    bin_lookup = {}
    for b in bins:
        # Subtract the edge kerf from both sides of the width and length to mimic edge-jointing waste
        bw = int((b['width'] - (2 * kerf)) * SCALE)
        bl = int((b['length'] - (2 * kerf)) * SCALE)
        
        # Guard against boards that are so small they disappear after milling
        if bw <= 0 or bl <= 0:
            continue
            
        for i in range(int(b.get('qty', 1))):
            # Using label if available
            label = b.get('label', str(b['id']))
            bin_uid = f"{label}_{i+1}"
            bin_lookup[bin_uid] = b
            packer.add_bin(bw, bl, bid=bin_uid)
            
    # Add Parts (Requirements)
    all_parts = []
    part_lookup = {}
    for p in parts:
        for i in range(int(p.get('qty', 1))):
            pw = int((p['width'] + kerf) * SCALE)
            pl = int((p['length'] + kerf) * SCALE)
            
            # Fallback for ID
            desc = str(p.get('desc', p['id']))
            # Avoid overly long strings 
            desc_short = desc[:15]
            part_uid = f"{desc_short}_{i+1}"
            
            part_lookup[part_uid] = p
            packer.add_rect(pw, pl, rid=part_uid)
            all_parts.append(part_uid)
            
    # Execute the algorithmic packing
    packer.pack()
    
    # Process Results
    packed_uids = set()
    packed_bins_data = [] 
    
    # Iterate through rects to identify packed items
    for b in packer.rect_list():
        bin_idx, x, y, w, h, part_uid = b
        packed_uids.add(part_uid)
        
    for abin in packer:
        bin_uid = abin.bid
        orig_bin = bin_lookup[bin_uid]
        rects = []
        for r in abin:
            x, y, w, h, rid = r.x, r.y, r.width, r.height, r.rid
            rects.append({
                'id': rid,
                # Offset by the kerf margin physically so it overlays correctly on the blueprint inside the boundary
                'x': (x / SCALE) + kerf,
                'y': (y / SCALE) + kerf,
                'width': (w / SCALE) - kerf,
                'length': (h / SCALE) - kerf
            })
        packed_bins_data.append({
            'bin_uid': bin_uid,
            'width': orig_bin['width'],
            'length': orig_bin['length'],
            'rects': rects
        })
        
    # Unpacked items -> Shopping List Items
    unpacked_uids = set(all_parts) - packed_uids
    unpacked_parts = []
    for uid in unpacked_uids:
        orig = part_lookup[uid]
        unpacked_parts.append({
            'uid': uid,
            'desc': orig['desc'],
            'width': orig['width'],
            'length': orig['length']
        })
                
    return {
        'packed_bins': packed_bins_data,
        'unpacked_parts': unpacked_parts
    }
