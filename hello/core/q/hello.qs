// Q# - Hello World! :: RAiNBOW_Hello-World
//   colour     : #fed659
//   hue        : 45.5 deg
//   layer      : core (byte-balanced rainbow bar)
//   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
//   reference  : see https://esolangs.org/ and https://rosettacode.org/

namespace Microsoft.Quantum.Samples {
    open Microsoft.Quantum.Intrinsic;
    @EntryPoint()
    operation Hello() : Unit {
        Message("Hello World!");
    }
}
