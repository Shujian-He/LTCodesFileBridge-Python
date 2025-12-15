import random
# import numpy as np
import math
import random
from collections import deque, defaultdict

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


def infinite_lt_encoder(file_data, block_size=1024):
    K = math.ceil(len(file_data) / block_size)
    # print("K", K)
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

def decode_lt_gpt(recovered, packets, K):
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

    if len(recovered) != K:
        print(f"Decoding failed: recovered {len(recovered)} blocks out of {K}")
        print("Recovered:", list(recovered.keys()))
        return None
    else:
        print("Decoding successful!")
    
    # Reassemble the original data in order.
    decoded_data = b''.join(recovered[i] for i in range(K))
    return decoded_data

# --- Main Demonstration ---
if __name__ == '__main__':
    # Read an example file
    filename = "output.txt"
    with open(filename, "rb") as f:
        original_data = f.read()

    encoder_gen = infinite_lt_encoder(original_data, 2048)
    encoded_packets = []
    count = 0
    recovered = {}
    
    while True:
        count += 1
        packet, K = next(encoder_gen)
        # print(K)
        encoded_packets.append(packet)
        decoded_data = decode_lt_gpt(recovered, encoded_packets, K)
        if decoded_data:
            break
    
    print(count)
    
    if decoded_data:
        decoded_data = decoded_data[:len(original_data)]
        with open(f"lt/{filename}", "wb") as f:
            f.write(decoded_data)
        assert decoded_data == original_data
    else:
        # print(len(decoded_data), len(original_data))
        print("Decoding failed.")
