# Adding a template: the wire formats

About twenty entries here are not languages at all. They are serialisation
formats, and the trap is that almost all of them *look* like text and only one of
them is.

## The trap

Every one of these has a "Hello World" that is tempting to write as text, and
the text version is a file the format's reader will reject. That is worse than a
placeholder: it looks finished, it passes every automated check in this
repository, and it does not load.

The reason is a single design decision per format. Pick the one that applies and
the answer follows:

| format | what it is | the answer |
|---|---|---|
| Protocol Buffers | a binary wire format with a `.proto` schema | **the schema**, not the message |
| Apache Thrift | IDL plus generated code | the IDL |
| Avro | JSON schema plus binary data | the schema |
| MessagePack | binary, like JSON but compact | a hex dump with computed bytes |
| CBOR | binary, self-describing, with text tags | a hex dump |
| BSON | binary, with a length-prefixed document | a hex dump |
| Cap'n Proto | zero-copy, with a schema | the schema |
| FlatBuffers | zero-copy, with a schema | the schema |
| JSON, YAML, TOML, XML | text | a document |

## The rule that decides it

**Does the format have a schema?** Then the schema is the program.

A Protocol Buffers `.proto` file is the interesting case, because it is *text*
and it is *not* a message:

```protobuf
syntax = "proto3";

package hello;

message Hello {
  string greeting = 1;
}
```

That is a complete, valid `.proto`. The corresponding binary message contains
field 1 as a length-delimited string — `0A 0C` then the twelve bytes — and
writing those bytes where the schema belongs produces a file protoc cannot
compile.

**Thrift** is the same argument:

```thrift
namespace cpp hello

service HelloService {
  string hello()
}
```

**Avro** and **JSON Schema** are the same again: the `.avsc` file is the schema.

## The formats with no schema at all

MessagePack, CBOR and BSON are self-describing — the data carries its own type
information — so there is no schema to write and the answer has to be the
encoded bytes.

Those three are already in this repository as computed hex dumps, produced by the
library that defines the format rather than written from memory, and verified by
`scripts/verify_encodings.py` decoding them back to the greeting. A BSON file
begins with a four-byte little-endian document length; a CBOR file's first byte is
the *type* of the first item, and `0x6F` is a text string of length 15. Neither
number is worth recalling from memory, which is why they were computed.

## Before you write one

- Does the format have a schema file? If so, the file is the schema. Writing
  encoded bytes where a schema belongs is the single most common wrong answer in
  this family.
- Is it self-describing — MessagePack, CBOR, BSON? Then there is no schema and
  the answer is the encoding, computed.
- Is it text? JSON, YAML, TOML, XML. Then the answer is a document.
- Does it carry a checksum, a length prefix, or a version byte? All three do, and
  all three have to be right; a dump written from memory is wrong in one byte and
  indistinguishable from correct.