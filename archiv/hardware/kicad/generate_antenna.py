#!/usr/bin/env python3
"""
KiCad Footprint Generator for 13.56 MHz Planar PCB Loop Antenna
Designed for 50x50mm Gridfinity Smart Mat (Active Area 40x40mm)
Parameters:
  - Size: 40 x 40 mm
  - Turns: 3
  - Track Width: 0.6 mm
  - Track Spacing: 0.5 mm
  - Target Inductance: ~1.35 uH
  - Layer: Top (F.Cu) with bottom return trace (B.Cu)
"""

import sys
import os

def generate_kicad_footprint(output_path):
    w = 0.6   # track width in mm
    s = 0.5   # spacing in mm
    turns = 3
    outer_size = 40.0
    half = outer_size / 2.0  # 20.0 mm

    lines = []
    lines.append('(footprint "RFID_Antenna_40x40_3T_13.56MHz"')
    lines.append('  (version 20240108)')
    lines.append('  (generator "Antigravity_RF_Antenna_Engine")')
    lines.append('  (layer "F.Cu")')
    lines.append('  (descr "13.56 MHz Planar Spiral Antenna 40x40mm 3 Turns for MFRC522 / NFC")')
    lines.append('  (tags "rfid nfc antenna 13.56mhz gridfinity planar coil")')
    lines.append('  (property "Reference" "ANT" (at 0 -22) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append('  (property "Value" "RFID_Antenna_1.35uH" (at 0 23) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')

    # Silk screen boundary
    b_half = half + 1.0
    lines.append(f'  (fp_rect (start -{b_half} -{b_half}) (end {b_half} {b_half}) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))')

    pitch = w + s  # 1.1 mm
    
    pad1_x = -2.5
    pad1_y = half
    pad2_x = 2.5
    pad2_y = half

    pts = [(pad1_x, pad1_y), (half, half)]
    cur_right = half
    cur_top = -half
    cur_left = -half
    cur_bottom = half - pitch

    for t in range(turns):
        pts.append((cur_right, cur_top))
        pts.append((cur_left, cur_top))
        pts.append((cur_left, cur_bottom))
        
        cur_right -= pitch
        cur_top += pitch
        cur_left += pitch
        cur_bottom -= pitch
        if t < turns - 1:
            pts.append((cur_right, pts[-1][1]))
        else:
            pts.append((cur_right, pts[-1][1]))

    # Draw F.Cu spiral lines
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i+1]
        lines.append(f'  (fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer "F.Cu"))')

    inner_end_x, inner_end_y = pts[-1]

    # Via to B.Cu at inner end
    lines.append(f'  (pad "" thru_hole circle (at {inner_end_x:.3f} {inner_end_y:.3f}) (size 1.0 1.0) (drill 0.4) (layers *.Cu))')

    # Via on B.Cu near Pad 2
    via2_x = pad2_x
    via2_y = pad2_y - 1.5
    lines.append(f'  (pad "" thru_hole circle (at {via2_x:.3f} {via2_y:.3f}) (size 1.0 1.0) (drill 0.4) (layers *.Cu))')

    # B.Cu return trace from inner via to via2
    lines.append(f'  (fp_line (start {inner_end_x:.3f} {inner_end_y:.3f}) (end {via2_x:.3f} {inner_end_y:.3f}) (stroke (width {w}) (type solid)) (layer "B.Cu"))')
    lines.append(f'  (fp_line (start {via2_x:.3f} {inner_end_y:.3f}) (end {via2_x:.3f} {via2_y:.3f}) (stroke (width {w}) (type solid)) (layer "B.Cu"))')

    # F.Cu short trace from via2 to Pad 2
    lines.append(f'  (fp_line (start {via2_x:.3f} {via2_y:.3f}) (end {pad2_x:.3f} {pad2_y:.3f}) (stroke (width {w}) (type solid)) (layer "F.Cu"))')

    # Connection Pads (SMD)
    lines.append(f'  (pad "1" smd rect (at {pad1_x:.3f} {pad1_y:.3f}) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))')
    lines.append(f'  (pad "2" smd rect (at {pad2_x:.3f} {pad2_y:.3f}) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask"))')

    lines.append(')')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"Footprint generated successfully: {output_path}")

if __name__ == "__main__":
    out = "hardware/kicad/RFID_Antenna_40x40_3T_13.56MHz.kicad_mod"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    generate_kicad_footprint(out)
