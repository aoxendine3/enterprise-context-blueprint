{
  description = "USENIX SAIS '27 Sovereign Falsification Suite // Lean 4 & Z3 Bit-Identical Differential Verifier";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    lean = {
      url = "github:leanprover/lean4/v4.35.0";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, lean }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        leanPkgs = lean.packages.${system};

        pythonEnv = pkgs.python311.withPackages (ps: [
          ps.z3
        ]);

        reproduceScript = pkgs.writeShellScriptBin "reproduce-proofs" ''
          set -euo pipefail
          export PATH="${leanPkgs.lean}/bin:${pkgs.z3}/bin:${pythonEnv}/bin:$PATH"
          echo "======================================================================"
          echo "NIX ISOLATED REPRODUCIBILITY RUNNER: USENIX SAIS '27 FALSIFICATION"
          echo "System: ${system} | Kernel: Lean v4.35.0 | Solver: Z3 ${pkgs.z3.version}"
          echo "======================================================================"
          exec ./reproduce.sh
        '';
      in
      {
        packages = {
          default = reproduceScript;
          falsification-suite = reproduceScript;
        };

        apps = {
          default = {
            type = "app";
            program = "${reproduceScript}/bin/reproduce-proofs";
          };
        };

        devShells.default = pkgs.mkShell {
          name = "sovereign-falsification-env";
          buildInputs = [
            leanPkgs.lean
            pkgs.z3
            pythonEnv
            pkgs.git
            pkgs.bash
          ];

          shellHook = ''
            echo "======================================================================"
            echo "SOVEREIGN FALSIFICATION ENVIRONMENT ACTIVE [NIX FLAKE]"
            echo "Lean 4: $(lean --version)"
            echo "Z3 SMT: $(z3 --version)"
            echo "Python: $(python3 --version)"
            echo "Run 'reproduce-proofs' or './reproduce.sh' to execute verification."
            echo "======================================================================"
          '';
        };
      }
    );
}
