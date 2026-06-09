// ZenPulse 腕带托板 — OpenSCAD 参数化原型
// 导出 STL: OpenSCAD → F6 → Export STL

length = 52;
width = 34;
thickness = 9;
arc_radius = 40;

sensor_pitch = 12;
sensor1_x = 14;
sensor2_x = sensor1_x + sensor_pitch;
sensor_y = width / 2;
led_hole_r = 2.75;
skirt_h = 1.5;
skirt_w = 2;
strap_slot_w = 22;
strap_slot_len = 14;

module rounded_bar() {
  hull() {
    for (dx = [0, length]) {
      for (dy = [0, width]) {
        translate([dx, dy, 0]) sphere(r = 1.2, $fn = 16);
      }
    }
  }
}

module strap_slots() {
  for (sx = [6, length - 6 - strap_slot_len]) {
    translate([sx, (width - strap_slot_w) / 2, -0.1])
      cube([strap_slot_len, strap_slot_w, thickness + 0.2]);
  }
}

module sensor_window(cx) {
  translate([cx, sensor_y, -0.1])
    cylinder(h = thickness + 0.2, r = led_hole_r, $fn = 32);
  for (a = [0:90:270]) {
    rotate([0, 0, a])
      translate([cx + led_hole_r + skirt_w / 2, sensor_y, thickness - skirt_h])
        cube([skirt_w, skirt_w, skirt_h + 0.1], center = true);
  }
}

difference() {
  intersection() {
    rounded_bar();
    translate([-5, -5, -arc_radius + 2])
      scale([1, 1, 1])
        translate([0, 0, arc_radius])
          rotate_extrude(angle = 60, convexity = 4)
            translate([arc_radius, 0, 0])
              square([thickness + 5, width + 10], center = true);
  }
  strap_slots();
  sensor_window(sensor1_x);
  sensor_window(sensor2_x);
}
