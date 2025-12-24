# Prototype code for encoding and decoding a file using LT codes

from tools import infinite_lt_encoder, lt_decoder

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
        recovered, encoded_packets = lt_decoder(encoded_packets)
        if len(recovered) == K:
            print("Decoding successful!")
            break
    
    # Reassemble the original data in order.
    decoded_data = b''.join(recovered[i] for i in range(K))
        # return decoded_data

    print(f"{count} packets used." )
    
    if decoded_data:
        decoded_data = decoded_data[:len(original_data)]
        with open(f"lt/{filename}", "wb") as f:
            f.write(decoded_data)
        assert decoded_data == original_data
    else:
        # print(len(decoded_data), len(original_data))
        print("Decoding failed.")
