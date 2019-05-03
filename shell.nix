{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [(python3.withPackages (p: with p;
    [ pandas matplotlib flask requests ]
  ))];
}
