"""
LT Codes Decoding Simulation

This module provides a simulation of the LT codes decoding process.
It implements an index-only version of the incremental peeling algorithm, which simulates
the recovery of input symbols from encoded packets without handling actual payload data.

The simulation demonstrates how LT codes work by tracking which input symbols are covered
by each packet and how the peeling process gradually recovers all original symbols through
iterative elimination of singleton packets.

Classes:
    IndexOnlyLTDecoder: Simulates the LT decoding process using only packet indices.

Functions:
    simulate_index_only_decoding: Runs the simulation with a list of packets and prints
                                  the step-by-step decoding process.
"""

from collections import defaultdict, deque

class IndexOnlyLTDecoder:
    """
    Incremental LT peeling simulator (index-only).
    This simulates only the evolution of packet indices,
    ignoring packet payloads entirely.
    """

    def __init__(self, k):
        self.k = k # k: Number of blocks
        self.recovered = set() # recovered input symbols
        self.packets = list() # residual packets: list of index lists
        self.block_to_packets = defaultdict(set) # {block : set of packet indices}
        self.ripple = deque() # queue of newly recovered blocks

    def add_packet(self, indices):
        """
        Add a new encoding symbol (index list only).
        """
        # Remove already recovered symbols
        new_indices = [i for i in indices if i not in self.recovered]

        if not new_indices:
            return

        packet_id = len(self.packets)
        self.packets.append(new_indices)

        for i in new_indices:
            self.block_to_packets[i].add(packet_id)

        # If singleton, release immediately
        if len(new_indices) == 1:
            self._add_to_ripple(new_indices[0])

        self._peel()

    def _add_to_ripple(self, block_idx):
        if block_idx not in self.recovered:
            self.ripple.append(block_idx)

    def _peel(self):
        """
        Incremental peeling process (index-only).
        """
        while self.ripple:
            b = self.ripple.popleft()
            if b in self.recovered:
                continue

            self.recovered.add(b)

            for packet_id in list(self.block_to_packets[b]):
                indices = self.packets[packet_id]
                if b not in indices:
                    continue

                indices.remove(b)
                self.block_to_packets[b].remove(packet_id)

                if len(indices) == 1:
                    self._add_to_ripple(indices[0])

    def is_complete(self):
        return len(self.recovered) == self.k
    
def simulate_index_only_decoding(packets, k):
    decoder = IndexOnlyLTDecoder(k)

    print("Starting incremental peeling simulation...\n")

    for step, indices in enumerate(packets, 1):
        print(f"--- Step {step}: adding packet {indices}")

        print("Packets before adding and peeling:")
        for i, p in enumerate(decoder.packets):
            print(f"  Packet {i}: {p}")
        
        decoder.add_packet(indices)

        print("Packets after adding and peeling:")
        for i, p in enumerate(decoder.packets):
            print(f"  Packet {i}: {p}")

        print(f"Recovered so far: {sorted(decoder.recovered)}\n")

        if decoder.is_complete():
            print("All input symbols recovered.")
            break

    print("Final recovered set:", sorted(decoder.recovered))
    return decoder.recovered

packets = [[7, 10, 1],
 [11, 9, 7, 1],
 [7, 11, 0, 3, 12, 5, 10],
 [0, 13, 2, 4],
 [0, 6],
 [13, 11],
 [11, 7],
 [6, 13, 1],
 [0, 7, 1, 10, 3],
 [9, 2, 0, 6, 1, 4, 5, 11, 3, 13, 10],
 [8, 1, 9, 2, 4, 12, 11, 0, 5],
 [12, 3, 10, 0, 9, 6, 13, 5],
 [4, 12],
 [3, 11],
 [2],
 [9, 5, 12],
 [9, 12, 4, 8, 3, 5, 0, 2, 6, 13, 1],
 [8, 11],
 [0, 6, 1],
 [3, 0],
 [2, 9],
 [11, 4, 3, 13, 10, 12, 5, 8, 1, 2, 9],
 [3, 11, 1, 10, 5],
 [4, 12],
 [8, 11, 2, 1, 10, 4, 12, 5, 9, 13],
 [7, 4, 6, 3, 0, 13, 10, 8, 9, 2, 5],
 [10, 2],
 [0, 1],
 [4, 5],
 [4, 6, 12, 13],
 [7, 1],
 [2, 8, 6, 13, 10, 11, 7, 5, 4, 0, 3],
 [6, 0],
 [0, 6, 13],
 [3],
 [11, 2, 13, 4, 1, 6, 12, 9, 10, 8, 7],
 [2, 4, 12],
 [3, 6],
 [0, 12, 5, 4, 7, 6, 10, 9, 2, 13, 1],
 [7, 9, 11, 3, 6, 4, 12]]

num_blocks = 14   # input symbols are 0..13

simulate_index_only_decoding(packets, num_blocks)