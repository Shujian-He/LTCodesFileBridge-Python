"""
This module provides functionality to read and decode QR codes that contain LT (Luby Transform)
codes packets, allowing for the recovery of the original file from a set of encoded packets.

The module includes functions to:
- Decode individual QR codes using pyzbar
- Convert bitmasks to block indices
- Decode LT packets from base64 encoded strings
- Process a sequence of QR codes to reconstruct the original file

When run as a main script, it reads QR codes from the 'qrcodes' directory,
decodes the LT packets, and writes the recovered file to the 'output' directory.
"""

import base64
import math
import os
from PIL import Image
import pyzbar.pyzbar as pyzbar
from pyzbar.pyzbar import ZBarSymbol
from tools import LTDecoder

def decode_qr_code_pyzbar(qr_path: str) -> bytes | None:
    """
    Decode a single QR code image and return raw bytes.
    """
    img = Image.open(qr_path)
    decoded_objects = pyzbar.decode(img, symbols=[ZBarSymbol.QRCODE])

    if not decoded_objects:
        return None

    return decoded_objects[0].data


def bitmask_to_indices(bitmask: bytes, num_blocks: int) -> list[int]:
    """
    Convert a bitmask (big-endian byte order) into block indices.
    """
    indices = []
    idx = 0

    for byte in reversed(bitmask):
        for bit in range(8):
            if idx >= num_blocks:
                return indices
            if byte & (1 << bit):
                indices.append(idx)
            idx += 1

    return indices


def decode_packet_with_bitmask(encoded_str: str, num_blocks: int):
    """
    Decode one LT packet from a base64 encoded string to this form:
        [bitmask][payload]
    and extract the indices and packet data.

    Returns:
        indices : list[int]
        packet  : bytes
    """
    combined = base64.b64decode(encoded_str)
    num_bytes = math.ceil(num_blocks / 8)
    bitmask = combined[0:num_bytes]
    indices = bitmask_to_indices(bitmask, num_blocks)
    packet = combined[num_bytes:]

    return indices, packet

if __name__ == "__main__":

    QR_DIR = "qrcodes"
    OUTPUT_DIR = "output"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --------------------------------------------------------
    # Step 1: Read header (QR 0)
    # --------------------------------------------------------
    header_bytes = decode_qr_code_pyzbar(os.path.join(QR_DIR, "0.png"))
    if header_bytes is None:
        raise RuntimeError("Failed to decode header QR code")

    header_str = header_bytes.decode("utf-8")
    _, file_name, file_size, num_blocks, block_size = header_str.split(":")

    file_size = int(file_size)
    num_blocks = int(num_blocks)
    block_size = int(block_size)

    print("Header decoded:")
    print("  File name :", file_name)
    print("  File size :", file_size)
    print("  Blocks    :", num_blocks)
    print("  Block size:", block_size)
    print()

    # --------------------------------------------------------
    # Step 2: Initialize decoder
    # --------------------------------------------------------
    decoder = LTDecoder(num_blocks)

    # --------------------------------------------------------
    # Step 3: Read packet QR codes incrementally
    # --------------------------------------------------------
    idx = 1
    while not decoder.is_complete():
        qr_path = os.path.join(QR_DIR, f"{idx}.png")
        if not os.path.exists(qr_path):
            print("No more QR codes available.")
            break

        raw = decode_qr_code_pyzbar(qr_path)
        if raw is None:
            print(f"Failed to decode QR {idx}")
            idx += 1
            continue

        indices, packet = decode_packet_with_bitmask(raw, num_blocks)
        decoder.add_packet(indices, packet)

        print(f"QR {idx}: degree={len(indices)}, recovered={len(decoder.recovered)}/{num_blocks}")
        idx += 1

    # --------------------------------------------------------
    # Step 4: Write recovered file
    # --------------------------------------------------------
    if decoder.is_complete():
        decoded_data = b''.join(decoder.recovered[i] for i in range(num_blocks))
        decoded_data = decoded_data[:file_size]


        output_path = os.path.join(OUTPUT_DIR, f"{file_name}")

        with open(output_path, "wb") as f:
            f.write(decoded_data)

        print("\nDecoding successful!")
        print(f"{idx-1} packet(s) used.")
        print("Recovered file written to:", output_path)
    else:
        print("\nDecoding failed: not enough packets.")