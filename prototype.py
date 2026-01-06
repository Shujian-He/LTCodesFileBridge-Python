"""
LT Codes Prototype Demonstration

This script demonstrates the complete LT codes encoding and decoding
workflow. It reads a file, encodes it into LT packets using the Robust Soliton Distribution,
then decodes the packets back to recover the original file, and verifies correctness.

The prototype shows:
1. File reading and LT encoding using the lt_encoder generator
2. Incremental decoding using the LTDecoder class
3. Packet-by-packet recovery until all blocks are decoded
4. Verification that the decoded data matches the original

This serves as a proof-of-concept for the LT codes implementation and can be used
as a reference for integrating LT coding into larger applications.
"""

from tools import lt_encoder, LTDecoder

if __name__ == '__main__':

    filename = "output.txt"
    with open(filename, "rb") as f:
        original_data = f.read()

    encoder_gen = lt_encoder(original_data)

    (indices, pkt), num_blocks = next(encoder_gen)

    decoder = LTDecoder(num_blocks)
    decoder.add_packet(indices, pkt)

    count = 1

    while not decoder.is_complete():
        (indices, pkt), _ = next(encoder_gen)

        decoder.add_packet(indices, pkt)
        count += 1

    print("Decoding successful!")
    print(f"{count} packets used.")

    decoded_data = b''.join(decoder.recovered[i] for i in range(num_blocks))
    decoded_data = decoded_data[:len(original_data)]

    with open(f"output/{filename}", "wb") as f:
        f.write(decoded_data)


    assert decoded_data == original_data