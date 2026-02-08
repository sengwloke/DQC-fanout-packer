# DQC-fanout-packer
A simple algorithm take takes a quantum circuit and generates an equivalent one with fanout operations (packing CNOTs into fanouts).

Why this matters for DQC / parity-based compilation

This packing step enables:
	•	Depth collapse of large parity layers
	•	Efficient use of GHZ / cat states
	•	Near-constant depth implementations of:
	•	QFT
	•	QAOA cost layers
	•	Stabilizer measurements
	•	Encrypted cloning / MISD-style fan-out


## What this algorithm is doing (intuitively)

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
Pseudocode:

function fanout_pack(fanout_ops):
    % fanout_ops: list of fanout operations
    % each fanout op = set of qubits {q1, q2, ..., qk}

    layers = empty list of layers

    for op in fanout_ops:
        placed = false

        # Try to place op into an existing layer
        for layer in layers:
            if not conflicts(op, layer):
                add op to layer
                placed = true
                break

        # If no compatible layer found, create a new one
        if not placed:
            new_layer = empty set
            add op to new_layer
            add new_layer to layers

    return layers


function conflicts(op, layer):
    for existing_op in layer:
        if share_qubit(op, existing_op):
            return true
    return false


function share_qubit(op1, op2):
    return (op1.qubit_set ∩ op2.qubit_set is not empty)

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
