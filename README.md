# DQC-fanout-packer
A simple algorithm take takes a quantum circuit and generates an equivalent one with fanout operations (packing CNOTs into fanouts).

Why this matters for DQC / parity-based compilation

This packing step enables:

	•	Depth collapse of large parity layers
	•	Efficient use of GHZ / cat states

Near-constant depth implementations of:
	•	QFT
	•	QAOA cost layers
	•	Encrypted cloning / MISD-style fan-out


# Note
We draw some inspiration from:
Efficient Gate Reordering for Distributed Quantum Compiling in Data Centers.
By Riccardo Mengoni(European Space Agency), Walter Nadalin(European Space Agency), Mathys Rennela(European Space Agency), Jimmy Rotureau(European Space Agency), Tom Darras(European Space Agency)Show All(8)
Jul 1, 2025
e-Print: 2507.01090 [quant-ph]



# What this algorithm is doing (intuitively)

### 1. Treat fan-outs as “jobs”

Each fan-out operation is treated as a *job* that requires exclusive access to the qubits it acts on.  
Two fan-out operations cannot be executed in the same layer if they share any qubit.

---

### 2. Build layers greedily

For each fan-out operation:

- Try to place it into the **earliest existing layer** where it does not conflict with any already placed fan-out
- If no such layer exists, **start a new layer**

This corresponds to a **greedy interval-packing / graph-coloring strategy**, where each layer represents a set of mutually compatible fan-out operations that can be executed in parallel.

---

### 3. Why greedy works well here

- Fan-out operations have **constant execution depth**, so minimizing the number of layers directly minimizes the overall circuit depth
- In **unbounded fan-out models**, greedy packing is often **asymptotically optimal**
- Finding an exact optimal coloring is **NP-hard**, whereas the greedy approach is simple, fast, and effective in practice

----

### Key ideas the algorithm uses

#### Safe reorder rules (typical)

To enable fan-out formation, the pass relies on safe gate reordering rules:

- **Disjoint-qubit commute:**  
  Gates acting on disjoint qubit sets commute and can be freely swapped.

- **Commuting families:**  
  Certain gate families commute even when sharing qubits.  
  Examples:
  - All **diagonal-in-Z** gates commute with each other.
  - Commuting Pauli-string phase operators.

- **Structure-aware commutation:**  
  Some structured two-qubit gates commute under specific conditions:
  - Controlled gates with the same control but different targets may commute.
  - Known rewrite identities (e.g., CNOT commuting patterns) can allow swaps.

#### FANOUT opportunities (typical)

The goal of reordering is to expose opportunities for fan-out compression:

- Many gates of the form  
  `CNOT(c → t₁), CNOT(c → t₂), ..., CNOT(c → tₖ)`  
  can be replaced by a single  
  `FANOUT(c → {t₁, t₂, ..., tₖ})`.

- Similarly, controlled-phase gates with the same control (and compatible angles) can be merged into a **multi-target phase fan-out**.

- In real circuits these gates are often **not adjacent** initially.  
  Reordering (via commutation) attempts to bring them together so they can be merged.


	------

	
### Example output:
	
C1 input : [CX(0→1), CX(2→3), CX(0→2), CX(0→3)]

C1 packed: [FANOUT(0→{1}), FANOUT(2→{3}), FANOUT(0→{2,3})]


C2 input : [CX(0→1), CX(0→2), CX(0→3), CX(0→1), CX(2→3)]

C2 packed: [FANOUT(0→{1,2,3}), FANOUT(0→{1}), FANOUT(2→{3})]


C3 input : [H(0,), CP(1.57)(1→0), CP(0.785)(2→0), CP(0.393)(3→0), H(1,)]

C3 packed: [H(0,), CP_FANOUT(1→{0:1.57}), CP_FANOUT(2→{0:0.785}), CP_FANOUT(3→{0:0.393}), H(1,)]


QFT4 input : [H(0,), CP(1.57)(0→1), CP(0.785)(0→2), CP(0.393)(0→3), H(1,), CP(1.57)(1→2), CP(0.785)(1→3), H(2,), CP(1.57)(2→3), H(3,)]

QFT4 packed: [H(0,), CP_FANOUT(0→{1:1.57,2:0.785,3:0.393}), H(1,), CP_FANOUT(1→{2:1.57,3:0.785}), H(2,), CP_FANOUT(2→{3:1.57}), H(3,)]
