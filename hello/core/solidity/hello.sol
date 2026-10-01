/*
Solidity - Hello World! :: RAiNBOW_Hello-World
  colour     : #aa6746
  hue        : 19.8 deg
  layer      : core (byte-balanced rainbow bar)
  upstream   : https://github.com/quxianp/RAiNBOW_Hello-World
  reference  : see https://esolangs.org/ and https://rosettacode.org/
*/

pragma solidity ^0.8.0;
contract Hello { function greet() public pure returns (string memory) { return "Hello World!"; } }
