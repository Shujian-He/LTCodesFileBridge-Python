# Helper to simulate the LT code decoding process given a set of packets

from collections import defaultdict, deque

def simulate_decode(packets):
    packets = [list(p) for p in packets]
    
    # block -> packets that reference it
    block_to_packets = defaultdict(set)
    for pkt_idx, indices in enumerate(packets):
        for i in indices:
            block_to_packets[i].add(pkt_idx)
            
    recovered = set()
    q = deque()
    
    # Initialize queue with singleton packets
    for pkt_idx, indices in enumerate(packets):
        if len(indices) == 1:
            q.append(indices[0])
            
    iteration = 1
    
    while q:
        block = q.popleft()

        iteration += 1

        if block in recovered:
            print(f"Iteration {iteration} skipped: Block {block} already recovered.")
            continue
        
        print(f"Iteration {iteration}: recovering block {block}")
        recovered.add(block)
        
        for pkt_idx in list(block_to_packets[block]):
            if block not in packets[pkt_idx]:
                continue
            
            packets[pkt_idx].remove(block)
            
            if len(packets[pkt_idx]) == 1:
                new_block = packets[pkt_idx][0]
                print(f"    New singleton formed: {new_block}")
                q.append(new_block)
                
        print("Packets after peeling:")
        for p in packets:
            print(p)
        
    print(f"Recovered blocks: {sorted(recovered)}")
    return recovered

# Provided index lists (each list simulates the indices of a packet)
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

simulate_decode(packets)
