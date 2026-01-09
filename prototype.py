"""
LT Codes Prototype Demonstration

This module demonstrates the complete LT codes encoding and decoding workflow. 
It reads a file, encodes it into LT packets using the Robust Soliton Distribution,
then decodes the packets back to recover the original file, and verifies correctness.

The prototype shows:
1. File reading and LT encoding using the lt_encoder generator
2. Incremental decoding using the LTDecoder class
3. Packet-by-packet recovery until all blocks are decoded
4. Verification that the decoded data matches the original
"""

from tools import lt_encoder, LTDecoder, choose_block_size, MAX_PAYLOAD_SIZE
import math

if __name__ == '__main__':

    file_name = "output.txt"
    with open(file_name, "rb") as f:
        original_data = f.read()

    block_size = choose_block_size(len(original_data), MAX_PAYLOAD_SIZE)
    num_blocks = math.ceil(len(original_data) / block_size)
    print(f"num_blocks = {num_blocks}")
    
    encoder_gen = lt_encoder(original_data, block_size)
    indices, pkt = next(encoder_gen)

    decoder = LTDecoder(num_blocks)
    decoder.add_packet(indices, pkt)

    count = 1

    while not decoder.is_complete():
        indices, pkt = next(encoder_gen)
        decoder.add_packet(indices, pkt)
        count += 1

    print("Decoding successful!")
    print(f"{count} packets used.")

    decoded_data = b''.join(decoder.recovered[i] for i in range(num_blocks))
    decoded_data = decoded_data[:len(original_data)]

    with open(f"output/{file_name}", "wb") as f:
        f.write(decoded_data)


    assert decoded_data == original_data