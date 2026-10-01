-- Agda - Hello World! :: RAiNBOW_Hello-World
--   colour     : #315665
--   hue        : 197.3 deg
--   layer      : core (byte-balanced rainbow bar)
--   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
--   reference  : see https://esolangs.org/ and https://rosettacode.org/

module hello where

postulate
  String : Set
  _≡_ : {A : Set} → A → A → Set
