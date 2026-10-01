-- VHDL - Hello World! :: RAiNBOW_Hello-World
--   colour     : #adb2cb
--   hue        : 230.0 deg
--   layer      : core (byte-balanced rainbow bar)
--   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
--   reference  : see https://esolangs.org/ and https://rosettacode.org/

library ieee;
use ieee.std_logic_1164.all;
entity hello is
end entity;
architecture rtl of hello is
begin
  process begin
    report "Hello World!" severity note;
    wait;
  end process;
end architecture;
