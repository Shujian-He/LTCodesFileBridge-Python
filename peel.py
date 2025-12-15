#!/usr/bin/env python3

def simulate_peeling(packets):
    # Make a deep copy of packets (each packet is a list of indices).
    packets = [list(p) for p in packets]
    recovered = set()
    iteration = 0
    
    while True:
        iteration += 1
        # Find all packets with exactly one index (singletons).
        singletons = [p[0] for p in packets if len(p) == 1]
        if not singletons:
            print(f"Iteration {iteration}: No singletons found, peeling stops.")
            break
        
        print(f"Iteration {iteration}: Singletons found: {singletons}")
        # Mark all found singletons as recovered.
        for s in singletons:
            recovered.add(s)
            
        # Peel (remove) all recovered indices from all packets.
        for i in range(len(packets)):
            # Remove any index that's already recovered.
            packets[i] = [x for x in packets[i] if x not in recovered]
            
        print(f"After iteration {iteration}, packets:")
        for p in packets:
            print(p)
        print("-" * 40)
        
    print("Recovered indices:", sorted(recovered))
    return recovered, packets

# Provided index lists (each list simulates the indices of a packet)
packets = [
[6, 11, 2, 12, 10] ,
[3, 6, 2] ,
[5, 3, 8, 4, 6, 13] ,
[4, 13, 2, 12, 10, 11] ,
[3, 2] ,
[5, 1] ,
[3, 9] ,
[11, 1, 8, 10] ,
[8, 10, 0, 3, 5, 13, 2, 9, 6, 7, 11, 4] ,
[8, 7, 11, 3, 10, 13, 9, 5] ,
[10, 2, 0, 11, 1, 9, 6, 3, 8, 13, 4, 5] ,
[4, 13, 1] ,
[3, 2, 12, 1, 0, 5, 6, 13, 11, 8, 9, 4, 7] ,
[6, 7, 10, 13, 1] ,
[9, 1, 0, 7, 2, 8] ,
[0, 10, 13, 2, 11] ,
[4, 3, 8] ,
[3, 6] ,
[6, 5] ,
[2] ,
[11, 8, 2, 9, 5, 1, 6, 3, 12, 7, 10] ,
[4, 13, 10, 0, 8, 1, 6] ,
[12, 11, 7] ,
[1, 9, 4] ,
[9, 3, 4, 6, 8, 2, 13, 1] ,
[6, 9] ,
[12, 0, 3, 7, 6] ,
[13, 0, 11, 2, 8, 5, 12] ,
]

simulate_peeling(packets)
