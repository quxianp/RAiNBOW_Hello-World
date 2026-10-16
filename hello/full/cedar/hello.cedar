// Cedar - Hello World! :: RAiNBOW_Hello-World
//   colour     : not assigned by Linguist
//   layer      : full (byte-balanced rainbow bar)
//   upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
//   reference  : see https://esolangs.org/ and https://rosettacode.org/

// Cedar is a policy language: a policy is a set of permits, and
// there is no output in it at all. The permit below is the one
// that says "Hello World!" may be read.
permit (
    principal == ?principal,
    action == "read",
    resource in ["Hello World!"]
);
