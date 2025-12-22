import random
import math
import random
from collections import deque, defaultdict
from tools import infinite_lt_encoder

def lt_decoder(recovered, packets, K):

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

    encoder_gen = infinite_lt_encoder(original_data)
    encoded_packets = []
    count = 0
    recovered = {}
    
    while True:
        count += 1
        packet, K = next(encoder_gen)
        # print(K)
        encoded_packets.append(packet)
        decoded_data = lt_decoder(recovered, encoded_packets, K)
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
