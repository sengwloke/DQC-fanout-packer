# Compiler to generate an equivalent circuit with packets of fanout operations

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple


# =====================================================
# Minimal gate representation
# =====================================================

@dataclass(frozen=True)
class Gate:
    """
    Gate types:
      - "cx":        qubits = (control, target)
      - "cp":        qubits = (control, target), params = (theta,)
      - "fanout":    qubits = (control, t1, t2, ...)
      - "cp_fanout": qubits = (control, t1, t2, ...), params = (theta1, theta2, ...)
      - others (e.g. "h", "rz") pass through unchanged
    """
    name: str
    qubits: Tuple[int, ...]
    params: Tuple[float, ...] = ()

    def __repr__(self) -> str:
        if self.name == "cx":
            c, t = self.qubits
            return f"CX({c}→{t})"
        if self.name == "cp":
            c, t = self.qubits
            th = self.params[0]
            return f"CP({th:.3g})({c}→{t})"
        if self.name == "fanout":
            c = self.qubits[0]
            ts = ",".join(map(str, self.qubits[1:]))
            return f"FANOUT({c}→{{{ts}}})"
        if self.name == "cp_fanout":
            c = self.qubits[0]
            pairs = ",".join(
                f"{t}:{th:.3g}" for t, th in zip(self.qubits[1:], self.params)
            )
            return f"CP_FANOUT({c}→{{{pairs}}})"
        if self.params:
            qs = ",".join(map(str, self.qubits))
            ps = ",".join(f"{p:.3g}" for p in self.params)
            return f"{self.name.upper()}({qs}; {ps})"
        return f"{self.name.upper()}{self.qubits}"


def CX(c: int, t: int) -> Gate:
    return Gate("cx", (c, t))


def CP(theta: float, c: int, t: int) -> Gate:
    return Gate("cp", (c, t), (theta,))


def FANOUT(c: int, targets: Iterable[int]) -> Gate:
    return Gate("fanout", (c,) + tuple(targets))


def CP_FANOUT(c: int, target_to_theta: Dict[int, float], order: List[int]) -> Gate:
    return Gate(
        "cp_fanout",
        (c,) + tuple(order),
        tuple(target_to_theta[t] for t in order),
    )


# =====================================================
# Commutation oracle
# =====================================================

def touched(g: Gate) -> Set[int]:
    return set(g.qubits)


def is_cx(g: Gate) -> bool:
    return g.name == "cx"


def is_cp(g: Gate) -> bool:
    return g.name == "cp"


def is_packetable(g: Gate) -> bool:
    return g.name in ("cx", "cp")


def is_diagonal(g: Gate) -> bool:
    return g.name in ("cp", "rz", "cp_fanout")


def commutes(g1: Gate, g2: Gate) -> bool:
    if is_diagonal(g1) and is_diagonal(g2):
        return True
    if touched(g1).isdisjoint(touched(g2)):
        return True
    return False


# =====================================================
# Sliding helpers
# =====================================================

def can_slide(C: List[Gate], packet_end: int, idx: int) -> bool:
    g = C[idx]
    for k in range(packet_end, idx):
        if not commutes(g, C[k]):
            return False
    return True


def bubble_left(C: List[Gate], src: int, dst: int):
    while src > dst:
        C[src - 1], C[src] = C[src], C[src - 1]
        src -= 1


# =====================================================
# FanoutPack for CX and CP
# =====================================================

def fanout_pack(C_in: List[Gate]) -> List[Gate]:
    C = list(C_in)
    i = 0

    while i < len(C):
        g = C[i]

        if not is_packetable(g):
            i += 1
            continue

        # -------- CX packets --------
        if is_cx(g):
            c, t0 = g.qubits
            targets = [t0]
            seen = {t0}

            start = i
            end = i + 1

            j = end
            while j < len(C):
                gj = C[j]
                if is_cx(gj) and gj.qubits[0] == c:
                    t = gj.qubits[1]
                    if t not in seen and can_slide(C, end, j):
                        bubble_left(C, j, end)
                        targets.append(t)
                        seen.add(t)
                        end += 1
                        j = end
                        continue
                j += 1

            del C[start:end]
            C.insert(start, FANOUT(c, targets))
            i = start + 1
            continue

        # -------- CP packets --------
        if is_cp(g):
            c, t0 = g.qubits
            theta0 = g.params[0]

            target_to_theta = {t0: theta0}
            order = [t0]

            start = i
            end = i + 1

            j = end
            while j < len(C):
                gj = C[j]
                if is_cp(gj) and gj.qubits[0] == c:
                    t = gj.qubits[1]
                    th = gj.params[0]
                    if can_slide(C, end, j):
                        bubble_left(C, j, end)
                        if t in target_to_theta:
                            target_to_theta[t] += th
                        else:
                            target_to_theta[t] = th
                            order.append(t)
                        end += 1
                        j = end
                        continue
                j += 1

            del C[start:end]
            C.insert(start, CP_FANOUT(c, target_to_theta, order))
            i = start + 1
            continue

    return C


# =====================================================
# Examples: C1, C2, C3, QFT4, CGR
# =====================================================

if __name__ == "__main__":
    import math

    # -------------------------
    # C1: 4-qubit counterexample
    # -------------------------
    C1 = [
        CX(0, 1),
        CX(2, 3),
        CX(0, 2),
        CX(0, 3),
    ]

    print("C1 input :", C1)
    print("C1 packed:", fanout_pack(C1))
    print()

    # -------------------------
    # C2: image-style example
    # -------------------------
    C2 = [
        CX(0, 1),
        CX(0, 2),
        CX(0, 3),
        CX(0, 1),
        CX(2, 3),
    ]

    print("C2 input :", C2)
    print("C2 packed:", fanout_pack(C2))
    print()

    # -------------------------
    # C3: small CP example
    # -------------------------
    C3 = [
        Gate("h", (0,)),
        CP(math.pi / 2, 1, 0),
        CP(math.pi / 4, 2, 0),
        CP(math.pi / 8, 3, 0),
        Gate("h", (1,)),
    ]

    print("C3 input :", C3)
    print("C3 packed:", fanout_pack(C3))
    print()

    # -------------------------
    # QFT4 (no swaps, CP form)
    # -------------------------
    QFT4 = [
    # --- q0 block ---
    Gate("h", (0,)),
    CP(math.pi / 2, 0, 1),
    CP(math.pi / 4, 0, 2),
    CP(math.pi / 8, 0, 3),

    # --- q1 block ---
    Gate("h", (1,)),
    CP(math.pi / 2, 1, 2),
    CP(math.pi / 4, 1, 3),

    # --- q2 block ---
    Gate("h", (2,)),
    CP(math.pi / 2, 2, 3),

    # --- q3 block ---
    Gate("h", (3,)),
    ]

    print("QFT4 input :", QFT4)
    print("QFT4 packed:", fanout_pack(QFT4))

    # -------------------------
    # Example with gate reordering
    # -------------------------
    theta = 0.3  # any angle
   
    CGR = [
      CX(0, 1),                 # CX(0→1)
      Gate("h",  (1,)),          # H(q2)
      CX(0, 2),                 # CX(0→2)
      Gate("rz", (2,), (theta,)),# RZ(theta)(q3)
      CX(0, 3),                 # CX(0→3)
    ]

    print("CGR input :", CGR)
    print("CGR packed:", fanout_pack(CGR))
