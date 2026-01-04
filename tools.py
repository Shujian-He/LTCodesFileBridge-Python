# Tool functions for LT codes encoding and decoding

import math
import random
from collections import deque, defaultdict

MAX_PAYLOAD_SIZE = 2210  # max payload size BEFORE base64 encoding in bytes (base64 makes it 4/3 times larger)
# 2212 * 4/3 = 2949.33 < 2953 (max QR code v40-L capacity), in practice, random 2212 bytes become 2952 bytes after base64 encoding, use 2210 to be safe
MAX_FILE_SIZE = 9785888  # max file size we can handle in bytes
# uses 1106 bytes to store 1106 * 8 = 8848 blocks' bitmask, leaving 2212 - 1106 = 1106 bytes for data
# 1106 * 8848 = 9785888 bytes

def robust_soliton_distribution(N, c=0.1, delta=0.5):
    """
    Computes the robust Soliton distribution for a block of N symbols using pure Python.
    
    Parameters:
      N     : int   - total number of input symbols.
      c     : float - constant parameter (tuning parameter for robustness).
      delta : float - failure probability.
      
    Returns:
      mu    : list  - a list of length N, where mu[d-1] is the probability
                      for degree d (d = 1, 2, ..., N).
    """
    # Compute the ripple parameter R.
    R = c * math.log(N / delta) * math.sqrt(N)
    
    # Determine the threshold K and ensure it does not exceed N.
    K = int(math.floor(N / R))
    K = min(K, N)  # Adjust K if necessary
    
    # Build the ideal Soliton distribution (rho):
    # rho(1) = 1/N, and for d >= 2, rho(d) = 1/(d*(d-1)).
    rho = [0] * N
    rho[0] = 1.0 / N
    for d in range(2, N + 1):
        rho[d - 1] = 1.0 / (d * (d - 1))
    
    # Build the tau distribution (robustifying part).
    tau = [0] * N
    for d in range(1, K):
        tau[d - 1] = R / (d * N)
    if K <= N:
        tau[K - 1] = R * math.log(R / delta) / N
    
    # Combine the two distributions.
    combined = [r + t for r, t in zip(rho, tau)]
    
    # Normalize so that the probabilities sum to 1.
    total = sum(combined)
    mu = [x / total for x in combined]
    
    return mu

def choose_degree(pdf, K):
    # Create a list of degrees [1, 2, ..., K]
    degrees = list(range(1, K + 1))
    # Use random.choices to select one degree according to the distribution pdf.
    return random.choices(degrees, weights=pdf, k=1)[0]

def cal_size(file_size, max_size):
    # Try different block sizes from (max_size-1) down to 1
    for block_size in reversed(range(1, max_size)):
        k = math.ceil(file_size / block_size)
        k_to_bytes = math.ceil(k / 8)  # bytes needed to store bitmask for k blocks
        # Condition: bitmask bytes + block size == max_size.
        if k_to_bytes + block_size == max_size:
            return k, block_size
    return None

def lt_encoder(file_data):
    K, block_size = cal_size(len(file_data), MAX_PAYLOAD_SIZE)
    blocks = [file_data[i * block_size:(i + 1) * block_size] for i in range(K)]
    pdf = robust_soliton_distribution(K)
    while True:
        d = choose_degree(pdf, K)
        indices = random.sample(range(K), d)
        
        # XOR the selected blocks
        packet = blocks[indices[0]].ljust(block_size, b'\x00')
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            packet = bytes(a ^ b for a, b in zip(packet, block))
        
        yield (indices, packet), K

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
    