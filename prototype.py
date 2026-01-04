from tools import lt_encoder, LTDecoder

if __name__ == '__main__':
    
    filename = "output.txt"
    with open(filename, "rb") as f:
        original_data = f.read()

    encoder_gen = lt_encoder(original_data)

    (indices, pkt), k = next(encoder_gen)

    decoder = LTDecoder(k)
    decoder.add_packet(indices, pkt)

    count = 1

    while not decoder.is_complete():
        (indices, pkt), _ = next(encoder_gen)

        decoder.add_packet(indices, pkt)
        count += 1

    print("Decoding successful!")
    print(f"{count} packets used.")

    decoded_data = b''.join(decoder.recovered[i] for i in range(k))
    decoded_data = decoded_data[:len(original_data)]

    with open(f"lt/{filename}", "wb") as f:
        f.write(decoded_data)


    assert decoded_data == original_data