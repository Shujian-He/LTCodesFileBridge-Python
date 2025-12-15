import random
import numpy as np
import qrcode
import base64
import matplotlib.pyplot as plt
import math
from tools import robust_soliton_distribution, choose_degree

MAX_QR_PAYLOAD_SIZE = 2210  # max payload size for a QR code

def cal_size(file_size, qr_size):
    # Try different block sizes from (qr_size-1) down to 1
    for block_size in reversed(range(1, qr_size)):
        k = math.ceil(file_size / block_size)
        k_to_bytes = math.ceil(k / 8)  # bytes needed to store bitmask for k blocks
        # Condition: bitmask bytes + block size == qr_size.
        if k_to_bytes + block_size == qr_size:
            return k, block_size
    return None

def infinite_lt_encoder(file_data):
    K, block_size = cal_size(len(file_data), MAX_QR_PAYLOAD_SIZE)
    blocks = [file_data[i * block_size:(i + 1) * block_size] for i in range(K)]
    while True:
        d = choose_degree(K)
        indices = random.sample(range(K), d)
        
        # XOR the selected blocks
        packet = blocks[indices[0]].ljust(block_size, b'\x00')
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            packet = bytes(a ^ b for a, b in zip(packet, block))
        
        yield indices, packet

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

def indices_to_bitmask(indices, K):
    """
    Convert a list of indices into a bitmask of length K (packed into bytes).
    Each bit corresponds to a block (0 means absent, 1 means present).
    """
    bitmask_int = 0
    for idx in indices:
        bitmask_int |= (1 << idx)
    # Calculate number of bytes needed to store K bits.
    num_bytes = math.ceil(K / 8)
    return bitmask_int.to_bytes(num_bytes, byteorder='big')

def encode_packet_with_bitmask(size, indices, packet, K):
    """
    Combine K, indices bitmask and the packet data.
    Returns a Base64 string suitable for embedding in a QR code.
    """
    # size_bit = size.to_bytes(3, byteorder='big')
    # K_bit = K.to_bytes(2, byteorder='big')
    bitmask = indices_to_bitmask(indices, K)
    print(' '.join(f'{byte:08b}' for byte in bitmask))
    combined = bitmask + packet
    return base64.b64encode(combined).decode('utf-8')

# --- Main Demonstration ---
if __name__ == '__main__':
    pass
    filename = "b.jpg"  # Change to your filename.
    with open(filename, "rb") as f:
        original_data = f.read()
    
    filesize = len(original_data)

    # Compute K from the file data.
    K, block_size = cal_size(filesize, MAX_QR_PAYLOAD_SIZE)

    print(f"Splitting file into {K} blocks")
    
    meta_str = f"HEADER:{filename}:{filesize}:{K}:{block_size}"

    # 1. Show a QR code that only contains K.
    plt.figure("Initial Image", figsize=(10, 8))
    plt.imshow(create_qr(meta_str, version=1), cmap='gray')
    plt.axis('off')
    plt.show()
    
    # 2. Now create an infinite generator of encoded packets.
    encoder_gen = infinite_lt_encoder(original_data)
    
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 8))

    # Infinite loop: show each new packet as a QR code.
    while True:
    # for _ in range(1,2):
        indices, packet = next(encoder_gen)
        # Optionally, print the indices to the console for debugging.
        print("Packet indices:", indices)
        # Convert the binary packet data to Base64.
        # b64_data = base64.b64encode(packet).decode('utf-8')
        b64_data = encode_packet_with_bitmask(filesize, indices, packet, K)
        
        ax.clear()
        ax.imshow(create_qr(b64_data), cmap='gray')
        plt.axis('off')
        plt.draw()
        plt.pause(0.1)