// Node-side Solidity compiler driver for the OAC genesis contract.
//
// The npm package "solc" ships a CLI shim whose --standard-json
// handling is unreliable (it prepends a diagnostic line and mis-parses
// the input file on Windows). The package's Node API, however, is the
// supported interface: it takes the input object and returns the output
// object.
//
// So this script is a thin, honest bridge: it reads the standard-JSON
// input from stdin, calls solc.compile, and writes the standard-JSON
// output to stdout. The Python test drives it and parses the result.
//
// Usage:  node compile_solidity.js <path-to-solc-package>
//         (input on stdin, output on stdout)

"use strict";

const fs = require("fs");
const path = require("path");

function fail(message) {
  process.stderr.write(message + "\n");
  process.exit(1);
}

const solcRoot = process.argv[2];
if (!solcRoot) {
  fail("usage: node compile_solidity.js <path-to-solc-package>");
}

let solc;
try {
  solc = require(path.join(solcRoot, "index.js"));
} catch (err) {
  fail("cannot load solc from " + solcRoot + ": " + err.message);
}

let raw;
try {
  raw = fs.readFileSync(0, "utf8");
} catch (err) {
  fail("cannot read stdin: " + err.message);
}

let input;
try {
  input = JSON.parse(raw);
} catch (err) {
  fail("stdin is not valid JSON: " + err.message);
}

let output;
try {
  output = JSON.parse(solc.compile(JSON.stringify(input)));
} catch (err) {
  fail("the compiler threw: " + (err && err.message ? err.message : String(err)));
}

process.stdout.write(JSON.stringify(output));
