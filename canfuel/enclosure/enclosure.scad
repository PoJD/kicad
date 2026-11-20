// canfuel — a two-part 3D-printed enclosure for the converter board.
//
// Everything here is derived from canfuel.kicad_pcb (board outline, hole
// positions, J1/J2 courtyards and pads) and from Molex SD-43045-001
// (docs/micro-fit-43045-datasheet.pdf). The reasoning is in
// docs/enclosure.md; this file only builds the shapes.
//
// Render one part at a time:
//   openscad -D 'part="bottom"' -o bottom.stl enclosure.scad
//   openscad -D 'part="lid"'    -o lid.stl    enclosure.scad
//   part="assembly" shows both with a stand-in board, for looking only.
//
// Coordinates: the board's corner at the J1/J2 edge, on the left when the
// board is seen from the component side with the connectors towards you, is
// (0,0). x runs along the connector edge, y away from it (KiCad's y flipped,
// so the picture is not mirrored), z up from the bottom face of the box.

part = "assembly";            // "bottom" | "lid" | "assembly" | "section"

// ---- the board (canfuel.kicad_pcb) ----------------------------------------
pcb_x = 55;                   // Edge.Cuts 50..105
pcb_y = 45;                   // Edge.Cuts 50..95
pcb_t = 1.5;                  // (general (thickness 1.5))
pcb_r = 2;                    // corner arcs
holes = [[4, 4], [51, 4], [4, 41], [51, 41]];   // H1..H4, M3, 3.2 mm

// J1 and J2: Micro-Fit 43045-0400 headers on the y = 0 edge, mating face
// 0.33 mm in from it (implementation-plan.md 3.7). Header body 9.65 wide and
// 7.37 tall over the board (SD-43045-001, A for 4 circuits; the side view).
// Centres from the footprints' peg holes: x 13.40 and 25.10.
conn_x       = [13.40, 25.10];
conn_w       = 9.65;
conn_h       = 7.37;

// ---- the space asked for (the owner, 19/11/2026) --------------------------
above = 17;                   // board top to the inside of the roof
below = 5;                    // board bottom to the top of the floor

// ---- printing and fit (decisions, docs/enclosure.md) ----------------------
wall    = 1.6;                // 4 perimeters of a 0.4 mm nozzle; the width
                              // across J1/J2's edge is what the vent limits
floor_t = 2.0;
roof_t  = 2.0;
gap     = 0.3;                // board edge to the inside of the wall
box_r   = 3;                  // outside corner radius
tongue   = false;             // a tongue at the seam wants wall >= 2.4; off
                              // for width, the four screws line the lid up
tongue_t = 1.0;               // the bottom's tongue, inner part of the wall
tongue_h = 2.0;               // how far it rises into the lid
fit      = 0.2;               // clearance between tongue and lid, per side
clamp    = 0.2;               // lid posts proud of the seam, so they clamp

// Fixing: a lid post presses the board onto a bottom post at each hole; one
// M3 x 25 screw goes down through the lid, the lid post, the board hole and
// into the bottom post.
fixing   = "tap";             // "insert": M3 heat-set insert, 4.0 mm hole
                              // "tap":    screw cut straight into the plastic
insert_d = 4.0;               // hole for an M3 x 5.7 insert (OD 4.6)
insert_l = 5.7;
tap_d    = 2.5;               // M3 machine screw or a 3.0 plastic screw cuts its thread
screw_d  = 3.4;               // clearance through the lid
head_d   = 6.0;               // M3 socket or pan head, for the spot face
post_bot_d = 7.0;             // under the board: nothing there but leads;
                              // 7 leaves 0.8 to the wall at gap 0.3
post_top_d = 6.0;             // over the board: R6 and J1 come within 3.8

// The connector slot: one opening for both plugs, open at the lid's lower
// edge so the lid goes on over plugs already in. The 43025 receptacle is not
// on disk, so its outline is not known: the slot is the two headers plus
// 1 mm each side and 12 mm tall, room for the receptacle's latch over the
// header's 7.37 (a decision, docs/enclosure.md).
slot_x0 = conn_x[0] - conn_w/2 - 1;
slot_x1 = conn_x[1] + conn_w/2 + 1;
slot_h  = 12;

// Strain relief: a ledge under the plugs with a tunnel for a cable tie, so a
// pull on the loom ends at the box, not at J1/J2's solder joints.
strain    = true;
ledge_len = 12;               // out from the outside of the front wall
ledge_top = 7.0;              // a little under the plugs (board top 8.5)
tie_y     = 7;                // tunnel centre, from the outside of the wall:
                              // round the plugs' bodies or just behind them
tie_w     = 4.5;              // for ties up to 3.6 mm wide
tie_h     = 2.0;

// Ventilation slots in the roof, and optional windows over the LEDs.
vents     = false;            // off at the owner's word, 20/11: dust, and no heat to move
vent_w    = 1.8;
vent_n    = 6;
vent_y0   = 6;                // first and last slot centre: the slots keep
vent_y1   = 31;               // to the connector half, the name gets the rest

// The name, engraved: on the roof over the slots, and on the ledge's front
// face. One colour; it shows by its shadow (the owner, 19/11/2026).
label       = "canfuel";
label_font  = "Liberation Sans:style=Bold";
label_depth = 0.6;            // three 0.2 mm layers
label_size  = vents ? 7 : 9;  // the roof's; under 5 a first layer closes it
label_y     = vents ? 39 : pcb_y / 2;   // over the slots, or the roof's middle
ledge_label_size = 4.5;
leds      = true; 
led_pos   = [[1.7, 30.5], [1.7, 20.5]];   // D1, D2

// ---- derived --------------------------------------------------------------
in_x0 = -gap;              in_y0 = -gap;
in_x1 = pcb_x + gap;       in_y1 = pcb_y + gap;
out_x0 = in_x0 - wall;     out_y0 = in_y0 - wall;
out_x1 = in_x1 + wall;     out_y1 = in_y1 + wall;

z_pcb_bot = floor_t + below;
z_seam    = z_pcb_bot + pcb_t;          // board top = where the parts meet
z_roof_in = z_seam + above;
z_top     = z_roof_in + roof_t;

$fn = 48;

module rrect(x0, y0, x1, y1, r, h) {
    translate([x0 + r, y0 + r, 0])
        linear_extrude(h)
            offset(r = r) square([x1 - x0 - 2*r, y1 - y0 - 2*r]);
}

// ---- bottom ---------------------------------------------------------------
module bottom() {
    t_in = wall - tongue_t;             // the tongue's inner face = the wall's
    difference() {
        union() {
            // shell up to the seam
            difference() {
                rrect(out_x0, out_y0, out_x1, out_y1, box_r, z_seam);
                translate([0, 0, floor_t])
                    rrect(in_x0, in_y0, in_x1, in_y1, 0.5, z_seam);
            }
            // tongue
            if (tongue) translate([0, 0, z_seam]) difference() {
                rrect(in_x0 - tongue_t, in_y0 - tongue_t,
                      in_x1 + tongue_t, in_y1 + tongue_t, 1, tongue_h);
                translate([0, 0, -1])
                    rrect(in_x0, in_y0, in_x1, in_y1, 0.5, tongue_h + 2);
            }
            // posts under the board
            for (h = holes) translate([h[0], h[1], 0])
                cylinder(d = post_bot_d, h = z_pcb_bot);
            if (strain) ledge();
        }
        // screw holes
        for (h = holes) translate([h[0], h[1], 0]) {
            if (fixing == "insert")
                translate([0, 0, z_pcb_bot - insert_l - 0.8])
                    cylinder(d = insert_d, h = insert_l + 1);
            else
                translate([0, 0, floor_t - 1])
                    cylinder(d = tap_d, h = z_pcb_bot);
        }
        // the slot through the tongue
        translate([slot_x0, out_y0 - 1, z_seam - 0.01])
            cube([slot_x1 - slot_x0, wall + 2, tongue_h + 1]);
    }
}

module ledge() {
    lx0 = slot_x0 - 3;  lx1 = slot_x1 + 3;
    difference() {
        translate([lx0, out_y0 - ledge_len, 0])
            cube([lx1 - lx0, ledge_len + wall / 2, ledge_top]);
        // the name on the front face, read from in front
        if (label != "")
            translate([(lx0 + lx1) / 2, out_y0 - ledge_len - 1, ledge_top / 2])
                rotate([90, 0, 0]) mirror([0, 0, 1])
                    linear_extrude(label_depth + 1)
                        text(label, size = ledge_label_size, font = label_font,
                             halign = "center", valign = "center");
        // tunnel for the tie, along x
        translate([lx0 - 1, out_y0 - tie_y - tie_w/2, ledge_top - 1.2 - tie_h])
            cube([lx1 - lx0 + 2, tie_w, tie_h]);
    }
}

// ---- lid ------------------------------------------------------------------
module lid() {
    h = z_top - z_seam;                 // lid height, seam to top
    difference() {
        union() {
            difference() {
                translate([0, 0, z_seam])
                    rrect(out_x0, out_y0, out_x1, out_y1, box_r, h);
                translate([0, 0, z_seam - 1])
                    rrect(in_x0, in_y0, in_x1, in_y1, 0.5, above + 1);
                // the rabbet the tongue goes into
                if (tongue) translate([0, 0, z_seam - 1])
                    rrect(in_x0 - tongue_t - fit, in_y0 - tongue_t - fit,
                          in_x1 + tongue_t + fit, in_y1 + tongue_t + fit,
                          1, tongue_h + fit + 1);
            }
            // posts over the board, a little proud of the seam
            for (p = holes) translate([p[0], p[1], z_seam - clamp])
                cylinder(d = post_top_d, h = above + clamp + 0.01);
        }
        for (p = holes) translate([p[0], p[1], 0]) {
            cylinder(d = screw_d, h = z_top + 1);
            // a 0.4 mm spot face, so the head sits on a flat ring
            translate([0, 0, z_top - 0.4]) cylinder(d = head_d + 1, h = 1);
        }
        // connector slot, open at the lower edge
        translate([slot_x0, out_y0 - 1, z_seam - clamp - 1])
            cube([slot_x1 - slot_x0, wall + 2, slot_h + clamp + 1]);
        if (vents) vent_slots();
        if (label != "")
            translate([pcb_x / 2, label_y, z_top - label_depth])
                linear_extrude(label_depth + 1)
                    text(label, size = label_size, font = label_font,
                         halign = "center", valign = "center");
        if (leds) for (l = led_pos)
            translate([l[0], l[1], z_roof_in - 1]) cylinder(d = 3.5, h = roof_t + 2);
    }
}

module vent_slots() {
    // across the middle of the roof, clear of the four posts
    x0 = 10;  x1 = pcb_x - 10;
    pitch = (vent_y1 - vent_y0) / (vent_n - 1);
    for (i = [0 : vent_n - 1])
        translate([x0, vent_y0 + i * pitch - vent_w / 2, z_roof_in - 1])
            hull() {
                translate([vent_w/2, vent_w/2, 0]) cylinder(d = vent_w, h = roof_t + 2);
                translate([x1 - x0 - vent_w/2, vent_w/2, 0]) cylinder(d = vent_w, h = roof_t + 2);
            }
}

// ---- a stand-in board, for the pictures only ------------------------------
module board() {
    color("darkgreen") translate([0, 0, z_pcb_bot]) difference() {
        rrect(0, 0, pcb_x, pcb_y, pcb_r, pcb_t);
        for (h = holes) translate([h[0], h[1], -1]) cylinder(d = 3.2, h = 4);
    }
    color("dimgray") for (c = conn_x)
        translate([c - conn_w/2, 0.33, z_seam]) cube([conn_w, 12.24, conn_h]);
    color("black") translate([10.9, 23.4, z_seam]) cube([35.2, 9.6, 8.5]);   // U1
    color("silver") translate([19.6, 34.2, z_seam]) cube([11, 4.7, 13.5]);  // Y1
}

module plugs() {
    color("white") for (c = conn_x)
        translate([c - conn_w/2 + 0.4, -14, z_seam + 0.6]) cube([conn_w - 0.8, 16, 9.5]);
}

if (part == "bottom") bottom();
else if (part == "lid") translate([0, pcb_y, z_top]) rotate([180, 0, 0]) lid();   // print roof down: turned over, never mirrored
else if (part == "section") difference() {
    union() { color("orange") bottom(); color("skyblue") lid(); board(); }
    translate([-50, -100 + holes[0][1], -1]) cube([200, 100, 100]);
}
else {
    color("orange") bottom();
    board(); plugs();
    color("skyblue", 0.55) translate([0, 0, 15]) lid();
}
