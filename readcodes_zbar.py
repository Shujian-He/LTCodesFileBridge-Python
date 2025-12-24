# Helpers to read QR codes using pyzbar and decode ONE LT code packet, for testing

import base64
import math
from PIL import Image
import pyzbar.pyzbar as pyzbar
from pyzbar.pyzbar import ZBarSymbol

def bitmask_to_indices(bitmask: bytes, K: int) -> list[int]:
    indices = []
    idx = 0

    # big-endian bytes → least-significant byte first
    for byte in reversed(bitmask):
        for bit in range(8):
            if idx >= K:
                return indices

            if byte & (1 << bit):
                indices.append(idx)

            idx += 1

    return indices

def decode_packet_with_bitmask(encoded_str, K):
    """
    Given a Base64 encoded string, extract the bitmask and packet data.
    Returns (indices, packet).
    """
    combined = base64.b64decode(encoded_str)
    num_bytes = math.ceil(K / 8)
    bitmask = combined[0:num_bytes]
    indices = bitmask_to_indices(bitmask, K)
    packet = combined[num_bytes:]

    return indices, packet

def decode_qr_code_pyzbar(qr_path):
    img = Image.open(qr_path)
    decoded_objects = pyzbar.decode(img, symbols=[ZBarSymbol.QRCODE])

    if not decoded_objects:
        return None

    return decoded_objects[0].data

if __name__ == '__main__':
    header_str = decode_qr_code_pyzbar("f0.png").decode("utf-8")
    
    _, file_name, file_size, K, block_size = header_str.split(":")
    file_size = int(file_size)
    K = int(K)
    block_size = int(block_size)


    content = decode_qr_code_pyzbar("f1.png")
    indices, packet = decode_packet_with_bitmask(content, K)
    print("File name:", file_name)
    print("File size:", file_size)
    print("K:", K)
    print("Packet indices:", indices)