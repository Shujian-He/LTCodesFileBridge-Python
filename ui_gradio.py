# Gradio-based UI for LT Codes Generator

import gradio as gr
import qrcode
import base64
import math
import random
import time
import os

# ---------------- Core logic ----------------

MAX_PAYLOAD_SIZE = 2210  # max payload size BEFORE base64 encoding in bytes (base64 makes it 4/3 times larger)
# 2212 * 4/3 = 2949.33 < 2953 (max QR code v40-L capacity), in practice, random 2212 bytes become 2952 bytes after base64 encoding, use 2210 to be safe
MAX_FILE_SIZE = 9785888  # max file size we can handle in bytes
# uses 1106 bytes to store 1106 * 8 = 8848 blocks' bitmask, leaving 2212 - 1106 = 1106 bytes for data
# 1106 * 8848 = 9785888 bytes

# Put every useful function here to ensure single-file execution
def robust_soliton_distribution(k: int, c: float = 0.1, delta: float = 0.5):
    """
    Compute the Robust Soliton Distribution as defined in:
    M. Luby, "LT Codes", The 43rd Annual IEEE Symposium on Foundations
    of Computer Science (FOCS), 2002.

    Parameters
    ----------
    k : int
        Number of input symbols (file blocks).
    c : float
        Positive constant controlling the average ripple size.
    delta : float
        Failure probability parameter (0 < delta < 1).

    Returns
    -------
    mu : list of float
        Probability mass function mu(d) for degrees d = 1, 2, ..., k.
        mu[d-1] corresponds to degree d.
    """

    # ------------------------------------------------------------
    # Step 1: Compute the ripple parameter R
    #
    #   R = c * ln(k / delta) * sqrt(k)
    #
    # This parameter controls the expected ripple size.
    # ------------------------------------------------------------
    R = c * math.log(k / delta) * math.sqrt(k)

    # ------------------------------------------------------------
    # Step 2: Compute the cutoff parameter K
    #
    #   K = floor(k / R)
    #
    # This determines where the robustifying distribution tau(d)
    # concentrates its mass.
    # ------------------------------------------------------------
    K = int(math.floor(k / R))
    K = min(K, k)

    # ------------------------------------------------------------
    # Step 3: Ideal Soliton Distribution rho(d)
    #
    #   rho(1) = 1 / k
    #   rho(d) = 1 / [d * (d - 1)],   for d = 2, ..., k
    # ------------------------------------------------------------
    rho = [0.0] * k
    rho[0] = 1.0 / k
    for d in range(2, k + 1):
        rho[d - 1] = 1.0 / (d * (d - 1))

    # ------------------------------------------------------------
    # Step 4: Robustifying distribution tau(d)
    #
    #   tau(d) = R / (d * k),                 for 1 <= d <= K - 1
    #   tau(K) = R * ln(R / delta) / k
    #   tau(d) = 0,                           for d > K
    # ------------------------------------------------------------
    tau = [0.0] * k
    for d in range(1, K):
        tau[d - 1] = R / (d * k)

    if K >= 1 and K <= k:
        tau[K - 1] = R * math.log(R / delta) / k

    # ------------------------------------------------------------
    # Step 5: Combine and normalize
    #
    #   mu(d) = (rho(d) + tau(d)) / Z
    #
    # where Z is the normalization constant.
    # ------------------------------------------------------------
    combined = [r + t for r, t in zip(rho, tau)]
    Z = sum(combined)
    mu = [x / Z for x in combined]

    return mu


def choose_degree(mu: list):
    """
    Sample a degree according to the Robust Soliton distribution.

    Parameters
    ----------
    mu : list of float
        Degree distribution for d = 1, 2, ..., k.

    Returns
    -------
    d : int
        Sampled degree.
    """

    return random.choices(
        population=range(1, len(mu) + 1),
        weights=mu,
        k=1
    )[0]


def validate_params(data_length: int, block_size: int):
    if data_length > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE} bytes)")

    if block_size <= 0:
        raise ValueError("block_size must be > 0")

    num_blocks = math.ceil(data_length / block_size)
    header_size = math.ceil(num_blocks / 8)

    if header_size + block_size > MAX_PAYLOAD_SIZE:
        raise ValueError(
            f"Invalid LT params: num_blocks={num_blocks}, block_size={block_size}, "
            f"payload={header_size + block_size} > {MAX_PAYLOAD_SIZE}"
        )

    return num_blocks


def lt_encoder(file_data: bytes, block_size: int):
    """
    LT Encoder generator function.
    The value num_blocks is computed once and yielded with every packet
    for convenience, but must be treated as a constant.
    """
    num_blocks = math.ceil(len(file_data) / block_size)

    blocks = [
        file_data[i * block_size:(i + 1) * block_size]
        for i in range(num_blocks)
    ]

    mu = robust_soliton_distribution(num_blocks)

    while True:
        d = choose_degree(mu)
        indices = random.sample(range(num_blocks), d)

        packet = bytearray(blocks[indices[0]].ljust(block_size, b'\x00'))
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            packet = bytes(a ^ b for a, b in zip(packet, block))

        yield indices, packet


def encode_packet_with_bitmask_web(indices: list, packet: bytes, num_blocks: int):
    """
    Convert a list of indices into a bitmask of length num_blocks / 8.
    Use big-endian byte order for better human readability.
    Then combine the bitmask and the packet data.
    Returns a Base64 string suitable for embedding in a QR code.
    """
    bitmask = bytearray(math.ceil(num_blocks / 8))
    for i in indices:
        bitmask[i // 8] |= 1 << (i % 8)
    bitmask.reverse()
    payload = bytes(bitmask) + packet
    return base64.b64encode(payload).decode('utf-8')


def create_qr_web(data: str):
    """
    Create a QR code image from the given data string.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=10, # quiet zone
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(
        fill_color="black",
        back_color="white"
    ).get_image()


# ---------------- Gradio UI logic ----------------

def prepare(file_path: str, block_size: int):
    # --- MODIFIED: file handling ---
    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        raw = f.read()

    # --- MODIFIED: explicit protocol params ---
    file_size = len(raw)

    num_blocks = validate_params(file_size, block_size)

    # --- MODIFIED: human-readable header ---
    meta_str = f"HEADER:{file_name}:{file_size}:{num_blocks}:{block_size}"
    header_qr = create_qr_web(meta_str)

    # --- MODIFIED: encoder uses raw bytes ---
    encoder = lt_encoder(raw, block_size)

    # --- MODIFIED: return FULL state ---
    state = {
        "encoder": encoder,
        "file_size": file_size,
        "num_blocks": num_blocks,
        "block_size": block_size,
        "file_name": file_name,
    }

    return header_qr, state


def stream_packets(state, running, rate):
    # Guard: stream_packets is called periodically even before Start is clicked
    if not running or state is None:
        return gr.update()

    encoder = state["encoder"]
    # file_size = state["file_size"]
    num_blocks = state["num_blocks"]
    # block_size = state["block_size"]

    update_interval = 1.0 / rate

    try:
        indices, packet = next(encoder)
    except StopIteration:
        return gr.update(value=None)
    except Exception as e:
        print("stream_packets error:", e)
        return gr.update(value=None)

    print(indices)
    b64 = encode_packet_with_bitmask_web(indices, packet, num_blocks)
    qr_img = create_qr_web(b64)
    time.sleep(update_interval)
    return qr_img


# ---------------- UI definition ----------------

with gr.Blocks(title="LT Codes Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 📡 LT Codes Generator
    Upload a file and continuously generate LT codes packets via QR codes.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Input File", type="filepath")
            block_size = gr.Slider(1, MAX_PAYLOAD_SIZE - 1, value=1500, step=1, label="Block size (bytes)")
            rate = gr.Slider(1.0, 5.0, value=5.0, step=1.0, label="QRs per second")
            start_btn = gr.Button("▶ Start", variant="primary")
            stop_btn = gr.Button("⏹ Stop", variant="secondary")
        with gr.Column(scale=1):
            header_qr = gr.Image(label="Header QR", type="pil")
            packet_qr = gr.Image(label="Packet QR", type="pil")

    state = gr.State()
    running = gr.State(False)

    def on_start(file, block_size, rate):
        header, state = prepare(file, block_size)
        return header, state, True # [header_qr, state, running]
    
    def on_stop():
        return False, None, None # [running, header_qr, packet_qr]

    start_btn.click(
        fn=on_start,
        inputs=[file_input, block_size, rate],
        outputs=[header_qr, state, running],
    )
    stop_btn.click(
        fn=on_stop,
        inputs=None,
        outputs=[running, header_qr, packet_qr],
    )

    demo.load(
        fn=stream_packets,
        inputs=[state, running, rate],
        outputs=packet_qr,
        every=0.2,
    )  # safe: stream_packets ignores empty state

if __name__ == "__main__":
    demo.launch(inbrowser=True, debug=True)
