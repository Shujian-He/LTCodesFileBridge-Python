# Show QR Codes with LT code packets (with header) using matplotlib

import qrcode
import base64
import matplotlib.pyplot as plt
import math
from tools import choose_block_size, lt_encoder, MAX_PAYLOAD_SIZE

# --- Helper: Show QR Code using plt ---
def create_qr(data_str, version=40):
    qr = qrcode.QRCode(
        version=version,  # Adjust if needed.
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    return img

def indices_to_bitmask(indices, num_blocks):
    """
    Convert a list of indices into a bitmask of length num_blocks / 8.
    Each bit corresponds to a block (0 means absent, 1 means present).
    Big-endian byte order.
    """
    bitmask = bytearray(math.ceil(num_blocks / 8))
    for i in indices:
        bitmask[i // 8] |= 1 << (i % 8)
    bitmask.reverse()
    return bytes(bitmask)

def encode_packet_with_bitmask(indices, packet, num_blocks):
    """
    Combine indices bitmask and the packet data.
    Returns a Base64 string suitable for embedding in a QR code.
    """
    bitmask = indices_to_bitmask(indices, num_blocks)
    print(' '.join(f'{byte:08b}' for byte in bitmask))
    combined = bitmask + packet
    return base64.b64encode(combined).decode('utf-8')

# --- Main Demonstration ---
if __name__ == '__main__':
    pass
    filename = "output.txt"
    with open(filename, "rb") as f:
        original_data = f.read()
    
    filesize = len(original_data)

    # Compute num_blocks from the file data.
    num_blocks, block_size = choose_block_size(filesize, MAX_PAYLOAD_SIZE)
    print(f"num_blocks={num_blocks}, block_size={block_size}")

    print(f"Splitting file into {num_blocks} blocks")
    
    meta_str = f"HEADER:{filename}:{filesize}:{num_blocks}:{block_size}"

    # 1. Show header QR code.
    plt.figure("Initial Image", figsize=(10, 8))
    plt.imshow(create_qr(meta_str, version=1), cmap='gray')
    plt.axis('off')
    plt.show()
    
    # 2. Now create an infinite generator of encoded packets.
    encoder_gen = lt_encoder(original_data)
    
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 8))

    # Infinite loop: show each new packet as a QR code.
    while True:
    # for _ in range(1,2):
        (indices, packet), _ = next(encoder_gen)
        # Optionally, print the indices to the console for debugging.
        print("Packet indices:", indices)
        # Convert the binary packet data to Base64.
        # b64_data = base64.b64encode(packet).decode('utf-8')
        b64_data = encode_packet_with_bitmask(indices, packet, num_blocks)
        print(len(b64_data))
        
        ax.clear()
        ax.imshow(create_qr(b64_data), cmap='gray')
        plt.axis('off')
        plt.draw()
        plt.pause(0.1)