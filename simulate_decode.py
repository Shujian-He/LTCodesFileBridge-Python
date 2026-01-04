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

        print("Packets before peeling:")
        for i, p in enumerate(decoder.packets):
            print(f"  Packet {i}: {p}")
        
        decoder.add_packet(indices)

        print("Packets after peeling:")
        for i, p in enumerate(decoder.packets):
            print(f"  Packet {i}: {p}")

        print(f"Recovered so far: {sorted(decoder.recovered)}\n")

        if decoder.is_complete():
            print("All input symbols recovered.")
            break

    print("Final recovered set:", sorted(decoder.recovered))
    return decoder.recovered

packets = [
    [6, 11, 2, 12, 10],
    [3, 6, 2],
    [5, 3, 8, 4, 6, 13],
    [4, 13, 2, 12, 10, 11],
    [3, 2],
    [5, 1],
    [3, 9],
    [11, 1, 8, 10],
    [8, 10, 0, 3, 5, 13, 2, 9, 6, 7, 11, 4],
    [8, 7, 11, 3, 10, 13, 9, 5],
    [10, 2, 0, 11, 1, 9, 6, 3, 8, 13, 4, 5],
    [4, 13, 1],
    [3, 2, 12, 1, 0, 5, 6, 13, 11, 8, 9, 4, 7],
    [6, 7, 10, 13, 1],
    [9, 1, 0, 7, 2, 8],
    [0, 10, 13, 2, 11],
    [4, 3, 8],
    [3, 6],
    [6, 5],
    [2],
    [11, 8, 2, 9, 5, 1, 6, 3, 12, 7, 10],
    [4, 13, 10, 0, 8, 1, 6],
    [12, 11, 7],
    [1, 9, 4],
    [9, 3, 4, 6, 8, 2, 13, 1],
    [6, 9],
    [12, 0, 3, 7, 6],
    [13, 0, 11, 2, 8, 5, 12],
    [0],
]

k = 14   # input symbols are 0..13

simulate_index_only_decoding(packets, k)