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

from tools import lt_encoder, LTDecoder, choose_block_size
import math

# unlike in qr code transmission, we can use any payload size here for demonstration
# we can set different sizes to see how it affects performance
MAX_PAYLOAD_SIZE = 1024

if __name__ == '__main__':

    # --------- Encoding ---------

    # Read original file
    file_name = "output.txt"
    with open(file_name, "rb") as f:
        original_data = f.read()

    # Determine block size and number of blocks
    block_size = choose_block_size(len(original_data), MAX_PAYLOAD_SIZE)
    num_blocks = math.ceil(len(original_data) / block_size)
    bitmask_size = math.ceil(num_blocks / 8)
    print(f"block_size = {block_size}, num_blocks = {num_blocks}, bitmask_size = {bitmask_size}")
    
    # Initialize LT encoder and generate first packet
    encoder_gen = lt_encoder(original_data, block_size)
    indices, pkt = next(encoder_gen)

    # --------- Decoding ---------

    # Initialize LT decoder and add first packet
    decoder = LTDecoder(num_blocks)
    decoder.add_packet(indices, pkt)

    count = 1

    # Continue adding packets until decoding is complete
    while not decoder.is_complete():
        indices, pkt = next(encoder_gen)
        decoder.add_packet(indices, pkt)
        count += 1

    print("Decoding successful!")
    print(f"{count} packets used.")

    # Verify recovered data matches original
    decoded_data = b''.join(decoder.recovered[i] for i in range(num_blocks))
    decoded_data = decoded_data[:len(original_data)]

    # Write recovered file for inspection
    with open(f"output/{file_name}", "wb") as f:
        f.write(decoded_data)

    assert decoded_data == original_data