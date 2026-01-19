"""
QR Code Display for LT Codes Packets

This module demonstrates the visualization of LT codes encoded as QR codes. 
It generates and displays QR codes containing:

1. A header QR code with file metadata (filename, size, block count, block size)
2. Sequential QR codes for each LT encoded packet, showing the bitmask and payload

Each packet QR code contains:
- A bitmask indicating which input blocks are XORed together
- The XORed payload data
- Base64 encoding for QR code compatibility

Functions:
    create_qr: Generates a QR code image from string data
    indices_to_bitmask: Converts block indices to a compact bitmask
    encode_packet_with_bitmask: Combines bitmask and payload into base64 string
"""

import qrcode
import matplotlib.pyplot as plt
import math
from tools import choose_block_size, encode_packet_with_bitmask, lt_encoder, MAX_PAYLOAD_SIZE

def create_qr(data_str: str, version=40):
    """
    Create a QR code image from the given data string.
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    return img

# --- Main Demonstration ---
if __name__ == '__main__':

    filename = "a.jpg"
    with open(filename, "rb") as f:
        original_data = f.read()
    
    filesize = len(original_data)

    # Compute num_blocks from the file data.
    block_size = choose_block_size(filesize, MAX_PAYLOAD_SIZE)
    num_blocks = math.ceil(filesize / block_size)
    print(f"num_blocks={num_blocks}, block_size={block_size}")

    print(f"Splitting file into {num_blocks} blocks")
    
    meta_str = f"HEADER:{filename}:{filesize}:{num_blocks}:{block_size}"

    # 1. Show header QR code.
    header_img = create_qr(meta_str, version=1)
    # header_img.save("qrcodes/0.png")

    plt.figure("Initial Image", figsize=(10, 8))
    plt.imshow(header_img, cmap='gray')
    plt.axis('off')
    plt.show()
    
    # 2. Now create an infinite generator of encoded packets.
    encoder_gen = lt_encoder(original_data, block_size)
    
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 8))

    packet_id = 1
    # Infinite loop: show each new packet as a QR code.
    while True:
        indices, packet = next(encoder_gen)
        print("Packet indices:", indices)
        
        b64_data = encode_packet_with_bitmask(indices, packet, num_blocks)
        print(len(b64_data))
        
        img = create_qr(b64_data)
        # img.save(f"qrcodes/{packet_id}.png")
        packet_id += 1
        
        ax.clear()
        ax.imshow(img, cmap='gray')
        plt.axis('off')
        plt.draw()
        plt.pause(0.1)