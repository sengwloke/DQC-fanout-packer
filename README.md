# DQC-fanout-packer
A simple algorithm take takes a quantum circuit and generates an equivalent one with fanout operations (packing CNOTs into fanouts).

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
