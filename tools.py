# Tool functions for LT codes encoding and decoding

import math
import random
from collections import deque, defaultdict

MAX_PAYLOAD_SIZE = 2210  # max payload size BEFORE base64 encoding in bytes (base64 makes it 4/3 times larger)
# 2212 * 4/3 = 2949.33 < 2953 (max QR code v40-L capacity), in practice, random 2212 bytes become 2952 bytes after base64 encoding, use 2210 to be safe
MAX_FILE_SIZE = 9785888  # max file size we can handle in bytes
# uses 1106 bytes to store 1106 * 8 = 8848 blocks' bitmask, leaving 2212 - 1106 = 1106 bytes for data
# 1106 * 8848 = 9785888 bytes

def robust_soliton_distribution(k, c=0.1, delta=0.5):
    """
    Compute the Robust Soliton Distribution as defined in:
    M. Luby, "LT Codes", The 43rd Annual IEEE Symposium on Foundations
    of Computer Science (FOCS), 2002.

    Parameters
    ----------
    k : int
        Number of input symbols (file blocks).
    c : float
        Positive constant controlling the average ripple size.
    delta : float
        Failure probability parameter (0 < delta < 1).

    Returns
    -------
    mu : list of float
        Probability mass function mu(d) for degrees d = 1, 2, ..., k.
        mu[d-1] corresponds to degree d.
    """

    # ------------------------------------------------------------
    # Step 1: Compute the ripple parameter R
    #
    #   R = c * ln(k / delta) * sqrt(k)
    #
    # This parameter controls the expected ripple size.
    # ------------------------------------------------------------
    R = c * math.log(k / delta) * math.sqrt(k)

    # ------------------------------------------------------------
    # Step 2: Compute the cutoff parameter K
    #
    #   K = floor(k / R)
    #
    # This determines where the robustifying distribution tau(d)
    # concentrates its mass.
    # ------------------------------------------------------------
    K = int(math.floor(k / R))
    K = min(K, k)

    # ------------------------------------------------------------
    # Step 3: Ideal Soliton Distribution rho(d)
    #
    #   rho(1) = 1 / k
    #   rho(d) = 1 / [d * (d - 1)],   for d = 2, ..., k
    # ------------------------------------------------------------
    rho = [0.0] * k
    rho[0] = 1.0 / k
    for d in range(2, k + 1):
        rho[d - 1] = 1.0 / (d * (d - 1))

    # ------------------------------------------------------------
    # Step 4: Robustifying distribution tau(d)
    #
    #   tau(d) = R / (d * k),                 for 1 <= d <= K - 1
    #   tau(K) = R * ln(R / delta) / k
    #   tau(d) = 0,                           for d > K
    # ------------------------------------------------------------
    tau = [0.0] * k
    for d in range(1, K):
        tau[d - 1] = R / (d * k)

    if K >= 1 and K <= k:
        tau[K - 1] = R * math.log(R / delta) / k

    # ------------------------------------------------------------
    # Step 5: Combine and normalize
    #
    #   mu(d) = (rho(d) + tau(d)) / Z
    #
    # where Z is the normalization constant.
    # ------------------------------------------------------------
    combined = [r + t for r, t in zip(rho, tau)]
    Z = sum(combined)
    mu = [x / Z for x in combined]

    return mu


def choose_degree(mu):
    """
    Sample a degree according to the Robust Soliton distribution.

    Parameters
    ----------
    mu : list of float
        Degree distribution for d = 1, 2, ..., k.

    Returns
    -------
    d : int
        Sampled degree.
    """

    return random.choices(
        population=range(1, len(mu) + 1),
        weights=mu,
        k=1
    )[0]

def choose_block_size(file_size, max_payload_size):
    """
    Choose the largest possible block size such that:
        ceil(k / 8) + block_size <= max_payload_size

    where:
        k = ceil(file_size / block_size)

    The bitmask is stored in front of the payload.
    """

    for block_size in range(max_payload_size - 1, 0, -1):
        k = math.ceil(file_size / block_size)
        bitmask_bytes = math.ceil(k / 8)

        if bitmask_bytes + block_size <= max_payload_size:
            return k, block_size

    raise ValueError("Cannot find a valid block size")

def lt_encoder(file_data):
    """
    LT Encoder generator function.
    The value k is computed once and yielded with every packet
    for convenience, but must be treated as a constant.
    """
    k, block_size = choose_block_size(len(file_data), MAX_PAYLOAD_SIZE)

    blocks = [
        file_data[i * block_size:(i + 1) * block_size]
        for i in range(k)
    ]

    mu = robust_soliton_distribution(k)

    while True:
        d = choose_degree(mu)
        indices = random.sample(range(k), d)

        packet = bytearray(blocks[indices[0]].ljust(block_size, b'\x00'))
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            for i in range(block_size):
                packet[i] ^= block[i]

        # k is constant across all yields
        yield (indices, bytes(packet)), k

class LTDecoder:
    """
    Incremental peeling decoder for LT Codes.
    This decoder maintains a residual bipartite graph and performs
    event-driven peeling as new encoding symbols arrive.
    """

    def __init__(self, k):
        """
        GRAPH EXAMPLE
        before:
            packets = [
                [6, 11, 2],   # packet 0
                [2],          # packet 1
                [3, 6]        # packet 2
            ]
        after:
            block_to_packets = {
                6:  {0, 2},
                11: {0},
                2:  {0, 1},
                3:  {2}
            }
        """
        self.k = k # k: Number of blocks
        self.recovered = defaultdict(set) # {block_idx : bytes} (immutable recovered symbols)
        self.packets = list() # residual packets: [[[indices], bytearray(data)], ...]
        self.block_to_packets = defaultdict(set) # {block : set of packet indices}
        self.ripple = deque() # queue of newly recovered blocks

    def add_packet(self, indices, pkt):
        """
        Add a newly received encoding symbol and trigger incremental peeling.

        :param indices: list of block indices participating in this packet
        :param pkt: XOR-ed payload of the selected blocks
        """
        # Residual packet must be mutable
        pkt = bytearray(pkt)

        # Step 1: Eliminate already recovered blocks
        new_indices = []
        for i in indices:
            if i in self.recovered:
                rec = self.recovered[i]
                pkt[:] = (a ^ b for a, b in zip(pkt, rec))
            else:
                new_indices.append(i)

        # If no unknown symbols remain, this packet carries no new information
        if not new_indices:
            return

        packet_id = len(self.packets)
        self.packets.append([new_indices, pkt])

        # Update adjacency structure
        for i in new_indices:
            self.block_to_packets[i].add(packet_id)

        # Step 2: If degree is 1, release a new block
        if len(new_indices) == 1:
            self._add_to_ripple(new_indices[0], pkt)

        # Step 3: Run the LT peeling process
        self._peel()

    def _add_to_ripple(self, block_idx, pkt):
        """
        Add a newly recovered block to the ripple.
        The recovered symbol must be immutable.
        """
        if block_idx not in self.recovered:
            # IMPORTANT: freeze the recovered symbol (no shared mutable buffer)
            self.recovered[block_idx] = bytes(pkt)
            self.ripple.append(block_idx)

    def _peel(self):
        """
        Perform the LT peeling process (incremental decoding).
        """
        while self.ripple:
            b = self.ripple.popleft()
            rec_pkt = self.recovered[b]

            # Process all encoding symbols that involve block b
            for packet_id in list(self.block_to_packets[b]):
                indices, pkt = self.packets[packet_id]
                if b not in indices:
                    continue

                # Remove b from this encoding symbol
                indices.remove(b)
                pkt[:] = (a ^ c for a, c in zip(pkt, rec_pkt))
                self.block_to_packets[b].remove(packet_id)

                # If degree drops to 1, release a new block
                if len(indices) == 1:
                    new_b = indices[0]
                    self._add_to_ripple(new_b, pkt)

    def is_complete(self):
        """
        Check whether all k blocks have been recovered.
        """
        return len(self.recovered) == self.k
    