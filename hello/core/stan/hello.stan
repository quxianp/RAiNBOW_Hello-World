// Stan - Hello World! :: RAiNBOW_Hello-World
//   colour     : #b2011d
//   hue        : 350.5 deg
//   layer      : core (byte-balanced rainbow bar)
//   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
//   reference  : see https://esolangs.org/ and https://rosettacode.org/

data { int<lower=0> N; }
parameters { real y; }
model { y ~ normal(0, 1); }
generated quantities { real y_sim = normal_rng(0, 1); }
