import base64
import math
from PIL import Image
import pyzbar.pyzbar as pyzbar
from pyzbar.pyzbar import ZBarSymbol
import glob

def bitmask_to_indices(bitmask, K):
    """
    Convert the bitmask (as bytes) back into a list of indices.
    """
    bitmask_int = int.from_bytes(bitmask, byteorder='big')
    indices = []
    for idx in range(K):
        if bitmask_int & (1 << idx):
            indices.append(idx)
    return indices

def decode_packet_with_bitmask(encoded_str, K):
    """
    Given a Base64 encoded string, extract the bitmask and packet data.
    Returns (K, indices, packet_data).
    """
    combined = base64.b64decode(encoded_str)

    # size_bit = combined[:3]
    # size = int.from_bytes(size_bit, byteorder='big')

    # K_bit = combined[3:3+2]
    # K = int.from_bytes(K_bit, byteorder='big')

    # num_bytes = math.ceil(K / 8) + 5
    # bitmask = combined[5:num_bytes]
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

    return decoded_objects[0].data  # read the first QR code content

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