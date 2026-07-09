import sys
import time
import numpy as np

class StabilizerSimulator:
    """
    A classical polynomial-time simulator for Clifford group quantum circuits
    based on the Gottesman-Knill theorem. Shows that classical systems CAN 
    efficiently simulate and verify highly entangled quantum states (e.g., Bell states,
    GHZ states) in polynomial time without simulating the full 2^N state-space.
    """
    def __init__(self, num_qubits):
        self.n = num_qubits
        # The stabilizer tableau has size 2n x (2n + 1)
        # Columns 0 to n-1: X stabilizer parts
        # Columns n to 2n-1: Z stabilizer parts
        # Column 2n: sign bit (0 for +, 1 for -)
        self.tableau = np.zeros((2 * self.n, 2 * self.n + 1), dtype=int)
        
        # Initialize tableau to identity stabilizers (Z_i for i, X_i for i+n)
        for i in range(self.n):
            self.tableau[i, i + self.n] = 1      # Z generators
            self.tableau[i + self.n, i] = 1      # X generators

    def h(self, qubit):
        """Apply Hadamard gate to the specified qubit (swaps X and Z, tracks signs)."""
        for i in range(2 * self.n):
            self.tableau[i, 2 * self.n] ^= (self.tableau[i, qubit] & self.tableau[i, qubit + self.n])
            tmp = self.tableau[i, qubit]
            self.tableau[i, qubit] = self.tableau[i, qubit + self.n]
            self.tableau[i, qubit + self.n] = tmp

    def phase(self, qubit):
        """Apply Phase gate S to the specified qubit (maps X to Y, leaves Z)."""
        for i in range(2 * self.n):
            self.tableau[i, 2 * self.n] ^= (self.tableau[i, qubit] & self.tableau[i, qubit + self.n])
            self.tableau[i, qubit + self.n] ^= self.tableau[i, qubit]

    def cx(self, control, target):
        """Apply CNOT gate from control to target."""
        for i in range(2 * self.n):
            self.tableau[i, 2 * self.n] ^= (self.tableau[i, control] & self.tableau[i, target + self.n] & 
                                            (self.tableau[i, target] ^ self.tableau[i, control + self.n] ^ 1))
            self.tableau[i, target] ^= self.tableau[i, control]
            self.tableau[i, control + self.n] ^= self.tableau[i, target + self.n]

    def get_state_stabilizers(self):
        """Returns readable string representations of the stabilizer generators (rows 0 to n-1 represent the state)."""
        generators = []
        # Stabilizers correspond to the first n rows of the tableau (indices 0 to n-1)
        for r in range(self.n):
            sign = '-' if self.tableau[r, 2 * self.n] else '+'
            op_strs = []
            for q in range(self.n):
                x = self.tableau[r, q]
                z = self.tableau[r, q + self.n]
                if x == 1 and z == 0:
                    op_strs.append('X')
                elif x == 0 and z == 1:
                    op_strs.append('Z')
                elif x == 1 and z == 1:
                    op_strs.append('Y')
                else:
                    op_strs.append('I')
            generators.append(f"{sign}{''.join(op_strs)}")
        return generators

def verify_ghz_state(num_qubits):
    """
    Creates and verifies a GHZ (Greenberger-Horne-Zeilinger) state (|00..0> + |11..1>) / sqrt(2).
    This state exhibits maximum multi-partite entanglement, yet Clifford simulation verifies it in O(N^2) time.
    """
    print(f"[*] Simulating maximally entangled GHZ State on {num_qubits} qubits...")
    t_start = time.perf_counter()
    
    sim = StabilizerSimulator(num_qubits)
    
    # 1. Apply Hadamard on first qubit to create superposition
    sim.h(0)
    
    # 2. Entangle all subsequent qubits with CNOT cascade
    for q in range(num_qubits - 1):
        sim.cx(q, q + 1)
        
    t_end = time.perf_counter()
    duration_ms = (t_end - t_start) * 1000
    
    stabilizers = sim.get_state_stabilizers()
    
    print(f"[+] Simulation completed in {duration_ms:.4f} ms.")
    print("[+] Verified Stabilizer Generators:")
    for idx, gen in enumerate(stabilizers):
        if idx < 10 or idx >= num_qubits - 2: # Keep output clean for large N
            print(f"    G_{idx}: {gen}")
        elif idx == 10:
            print("    ...")
            
    # Verify expected stabilizers: 
    # For a GHZ state, stabilizers are:
    # 1. X_0 * X_1 * ... * X_{N-1} (which is generator G_0)
    # 2. Z_i * Z_{i+1} for all i (which are generators G_1 through G_{N-1})
    # Let's verify G_0 has the X_0*...*X_{N-1} correlation
    has_all_x = stabilizers[0].startswith('+') and all(c == 'X' for c in stabilizers[0][1:])
    print(f"[+] Integrity Check: Global X-correlation verified = {has_all_x}")

def verify_bell_state():
    """
    Creates and verifies a two-qubit maximally entangled Bell state: (|00> + |11>) / sqrt(2).
    Stabilizer generators must be +XX and +ZZ.
    """
    print("[*] Simulating two-qubit Bell State...")
    sim = StabilizerSimulator(2)
    sim.h(0)
    sim.cx(0, 1)
    stabilizers = sim.get_state_stabilizers()
    print("[+] Verified Bell Stabilizers:")
    for idx, gen in enumerate(stabilizers):
        print(f"    G_{idx}: {gen}")
    
    has_xx = "+XX" in stabilizers
    has_zz = "+ZZ" in stabilizers
    print(f"[+] Integrity Check: Bell state correlation (+XX and +ZZ) = {has_xx and has_zz}")

if __name__ == "__main__":
    # 1. Test two-qubit Bell State
    verify_bell_state()
    print("\n" + "="*50 + "\n")
    # 2. Test with 10 qubits (highly entangled GHZ)
    verify_ghz_state(10)
    print("\n" + "="*50 + "\n")
    # 3. Test scaling by doing 100 qubits (normally 2^100 states, impossible classically without stabilizer theory)
    verify_ghz_state(100)
