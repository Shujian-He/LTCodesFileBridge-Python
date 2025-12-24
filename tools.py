# Tool functions for LT codes encoding and decoding

import math
import random
from collections import deque, defaultdict

MAX_PAYLOAD_SIZE = 2212  # max payload size BEFORE base64 encoding in bytes (base64 makes it 4/3 times larger)
# 2212 * 4/3 = 2949.33 < 2953 (max QR code v40-L capacity), in practice, random 2212 bytes become 2952 bytes after base64 encoding
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

def choose_degree(K):
    pdf = robust_soliton_distribution(K)
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

def infinite_lt_encoder(file_data):
    K, block_size = cal_size(len(file_data), MAX_PAYLOAD_SIZE)
    blocks = [file_data[i * block_size:(i + 1) * block_size] for i in range(K)]
    while True:
        d = choose_degree(K)
        indices = random.sample(range(K), d)
        
        # XOR the selected blocks
        packet = blocks[indices[0]].ljust(block_size, b'\x00')
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            packet = bytes(a ^ b for a, b in zip(packet, block))
        
        yield (indices, packet), K

def lt_decoder(packets):
    recovered = dict()  # block_idx -> packet data
    packets = [list(p) for p in packets]

    # Construct a mapping from block indices to the set of packet indices that include them.
    '''
    EXAMPLE
    before:
        packets = [
            [6, 11, 2],   # packet 0
            [2],          # packet 1
            [3, 6]        # packet 2
        ]
    after:
        block_idx_to_packets = {
            6:  {0, 2},
            11: {0},
            2:  {0, 1},
            3:  {2}
        }
    '''
    block_idx_to_packets = defaultdict(set)
    for packet_idx, (indices, _) in enumerate(packets):
        for idx in indices:
            block_idx_to_packets[idx].add(packet_idx)
    
    # Initialize a processing queue with packet indices that are immediately decodable.
    # A packet is decodable if it involves exactly one block index.
    q = deque()
    for keys in recovered:
        q.append(keys)
    for indices, pkt in packets:
        if len(indices) == 1:
            block_idx = indices[0]
            if block_idx not in recovered:
                recovered[block_idx] = pkt
                q.append(block_idx)
    
    # Process recovered blocks until the queue is empty.
    while q:
        recovered_block_idx = q.popleft()
        rec_pkt = recovered[recovered_block_idx]
        # Use a list() copy since we will modify the set during iteration.
        for packet_idx in list(block_idx_to_packets[recovered_block_idx]):
            indices, pkt = packets[packet_idx]
            if recovered_block_idx not in indices:
                continue  # It may have been updated already.
            # Remove the recovered index from the packet's index list.
            new_indices = [i for i in indices if i != recovered_block_idx]
            # Update the packet by XOR-ing with the recovered block.
            new_pkt = bytearray(a ^ b for a, b in zip(pkt, rec_pkt))
            packets[packet_idx] = (new_indices, new_pkt)
            
            # Remove this packet from the mapping for the recovered index.
            block_idx_to_packets[recovered_block_idx].remove(packet_idx)
            
            # If this update makes the packet decodable, add its block to recovered.
            if len(new_indices) == 1:
                new_block_idx = new_indices[0]
                if new_block_idx not in recovered:
                    recovered[new_block_idx] = new_pkt
                    q.append(new_block_idx)

    return recovered, packets
