-- Xmake - Hello World! :: RAiNBOW_Hello-World
--   colour     : #22a079
--   hue        : 161.4 deg
--   layer      : core (byte-balanced rainbow bar)
--   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
--   reference  : see https://esolangs.org/ and https://rosettacode.org/

target("hello")
    set_kind("phony")
on_run(function () print("Hello World!") end)
