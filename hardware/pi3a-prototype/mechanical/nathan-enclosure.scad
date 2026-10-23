// NATHAN D0 — rebuilt parametric enclosure, not a production model.
// Author: Codex/OpenAI nathan_bom. Units: mm.
// No imported STL/SLDPRT; only a measured 2D profile guides the new solids.
// Generated parameters retain explicit source/provisional status in design.json.
include <parameters.scad>

part = "assembly"; // assembly, top, bottom, controls_pcb, base_pcb, reservations
$fn = 48;

module outline(inset=0, factor=1) {
    scale([factor,factor]) offset(delta=-inset) polygon(shell_profile);
}

module rounded_body(inset=0, zlow=0, zhigh=shell_height) {
    // Piecewise tapered extrusion preserves the concave controller outline.
    // A convex hull of the whole profile would incorrectly fill its notches.
    taper = min(8,(zhigh-zlow)/3);
    translate([0,0,zlow]) linear_extrude(taper,scale=1/.94) outline(inset,.94);
    translate([0,0,zlow+taper]) linear_extrude(zhigh-zlow-2*taper) outline(inset,1);
    translate([0,0,zhigh-taper]) linear_extrude(taper,scale=.96) outline(inset,1);
}

module shell_solid() {
    difference() {
        rounded_body();
        rounded_body(wall,wall,shell_height-wall);
        // Cutouts are disabled until actual caps/stems/connectors are measured.
        if(enable_control_cutouts) {
            for(p=joysticks) translate([p[0],p[1],shell_height-8]) cylinder(h=10,d=24);
            // Two distinct four-button cardinal groups, plus two central controls.
            for(p=face_switches) translate([p[0],p[1],shell_height-8]) cylinder(h=10,d=13);
            for(p=central_switches) translate([p[0],p[1],shell_height-8]) cylinder(h=10,d=13);
        }
        if(enable_port_cutouts) {
            translate([usb_position[0]-5,usb_position[1]-8,usb_position[2]-2.5]) cube([10,16,5]);
            translate(jack_position) rotate([90,0,0]) cylinder(h=20,d=7,center=true);
        }
    }
}

module top() {
    intersection() { shell_solid(); translate([-200,-200,seam_z]) cube([400,400,200]); }
}

module bottom() {
    intersection() { shell_solid(); translate([-200,-200,-.1]) cube([400,400,seam_z+.1]); }
    // Alignment lip is only a parametric design proposal; no fit claim.
    translate([0,0,seam_z-.1]) linear_extrude(lip_height) difference() {
        outline(wall+lip_clearance);
        outline(wall+lip_clearance+1.2);
    }
    if(enable_mounting_bosses)
        for(p=base_mounts) translate([p[0],p[1],wall]) difference() {
            cylinder(h=base_z-wall,d=6);
            translate([0,0,-.1]) cylinder(h=base_z-wall+.2,d=2.7);
        }
}

module pcb(profile,z,holes) {
    translate([0,0,z]) linear_extrude(pcb_thickness) difference() {
        polygon(profile);
        for(p=holes) translate(p) circle(d=2.7);
    }
}

module reserve(xy,size,z) {
    translate([xy[0]-size[0]/2,xy[1]-size[1]/2,z]) cube(size);
}

module reservations() {
    color([.3,.5,.8,.35]) reserve(pi_xy,pi_size,pi_z);
    color([.8,.4,.2,.35]) reserve(sugar_xy,sugar_size,sugar_z);
    color([1,0,0,.45]) reserve(audio_xy,audio_size,audio_z); // unqualified module envelope
    for(p=joysticks) color([.4,.4,.4,.5]) reserve(p,joystick_size,controls_z+pcb_thickness);
    // Button-cap and shoulder shapes are reserved volumes, not qualified parts.
    for(p=face_switches) color([.2,.3,.7,.6]) translate([p[0],p[1],shell_height-2]) cylinder(h=4,d=13);
    for(p=central_switches) color([.4,.4,.4,.6]) translate([p[0],p[1],shell_height-2]) cylinder(h=4,d=13);
    // L1/R1 above L2/R2 in the same front shoulder projection.
    // There are no functional pivots, springs, sensor mounts or travel clearances yet.
    for(p=shoulder_bumpers) color([.2,.4,.7,.5]) reserve([p[0],p[1]],bumper_size,p[2]);
    for(p=shoulder_triggers) color([.2,.6,.7,.5]) reserve([p[0],p[1]],trigger_size,p[2]);
    for(p=motors) color([.8,.2,.8,.5]) translate([p[0],p[1],controls_z-3.25]) cylinder(h=3.25,d=8);
}

if(part=="top") top();
else if(part=="bottom") bottom();
else if(part=="controls_pcb") pcb(controls_outline,controls_z,controls_mounts);
else if(part=="base_pcb") pcb(base_outline,base_z,base_mounts);
else if(part=="reservations") reservations();
else {
    color([.6,.6,.6,.25]) top();
    color([.3,.3,.3,.3]) bottom();
    color([.1,.5,.2,.8]) pcb(controls_outline,controls_z,controls_mounts);
    color([.1,.4,.2,.8]) pcb(base_outline,base_z,base_mounts);
    reservations();
}
