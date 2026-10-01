-- PureScript - Hello World! :: RAiNBOW_Hello-World
--   colour     : #1d222d
--   hue        : 221.2 deg
--   layer      : core (byte-balanced rainbow bar)
--   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
--   reference  : see https://esolangs.org/ and https://rosettacode.org/

module Main where
import Prelude
import Effect (Effect)
import Effect.Console (log)

main :: Effect Unit
main = log "Hello World!"
