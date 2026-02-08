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


What this algorithm is doing (intuitively)

1. Treat fan-outs as “jobs”

Each fan-out operation is a job that needs exclusive access to its qubits.

⸻

2. Build layers greedily

For each fan-out:
	•	Try to fit it into the earliest layer where it does not conflict
	•	If it can’t fit anywhere, start a new layer

This is a greedy interval-packing / coloring strategy.

⸻

3. Why greedy works well here
	•	Fan-out depth is constant, so minimizing the number of layers minimizes total depth
	•	In unbounded fan-out models, this greedy approach is often asymptotically optimal
	•	Exact optimal coloring is NP-hard, but greedy is fast and effective

----
Pseudocode:

function fanout_pack(fanout_ops):
    # fanout_ops: list of fanout operations
    # each fanout op = set of qubits {q1, q2, ..., qk}

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
