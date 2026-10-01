/*
Zig - Hello World! :: RAiNBOW_Hello-World
  colour     : #ec915c
  hue        : 22.1 deg
  layer      : core (byte-balanced rainbow bar)
  upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
  reference  : see https://esolangs.org/ and https://rosettacode.org/
*/

const std = @import("std");

pub fn main() !void {
    std.debug.print("Hello World!\n", .{});
}
