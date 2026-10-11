; SMT - Hello World! :: RAiNBOW_Hello-World
;   colour     : not assigned by Linguist
;   layer      : full (byte-balanced rainbow bar)
;   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
;   reference  : see https://esolangs.org/ and https://rosettacode.org/

(set-logic QF_LIA)
(declare-fun hello () String)
(assert (= hello "Hello World!"))
(check-sat)
