// Cuda - Hello World! :: RAiNBOW_Hello-World
//   colour     : #3a4e3a
//   hue        : 120.0 deg
//   layer      : core (byte-balanced rainbow bar)
//   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
//   reference  : see https://esolangs.org/ and https://rosettacode.org/

__global__ void hello() {
  printf("Hello World!");
}
