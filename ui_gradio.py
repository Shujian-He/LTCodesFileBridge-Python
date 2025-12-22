# Gradio-based UI
# Focus: cleaner layout, better state handling, start/stop control, and stability

import gradio as gr
import qrcode
import base64
import math
import random
import time
import os

# ---------------- Core logic ----------------

MAX_QR_PAYLOAD_SIZE = 2210  # bytes


def robust_soliton_distribution(N, c=0.1, delta=0.5):
    """
    Computes the robust Soliton distribution for a block of N symbols using pure Python.
    
    Parameters:
      N     : int   - total number of input symbols.
      c     : float - constant parameter (tuning parameter for robustness).
      delta : float - failure probability.
      
    Returns:
      mu    : list  - a list of length N, where mu[d-1] is the probability
                      for degree d (d = 1, 2, ..., N).
    """
    # Compute the ripple parameter R.
    R = c * math.log(N / delta) * math.sqrt(N)
    
    # Determine the threshold K and ensure it does not exceed N.
    K = int(math.floor(N / R))
    K = min(K, N)  # Adjust K if necessary
    
    # Build the ideal Soliton distribution (rho):
    # rho(1) = 1/N, and for d >= 2, rho(d) = 1/(d*(d-1)).
    rho = [0] * N
    rho[0] = 1.0 / N
    for d in range(2, N + 1):
        rho[d - 1] = 1.0 / (d * (d - 1))
    
    # Build the tau distribution (robustifying part).
    tau = [0] * N
    for d in range(1, K):
        tau[d - 1] = R / (d * N)
    if K <= N:
        tau[K - 1] = R * math.log(R / delta) / N
    
    # Combine the two distributions.
    combined = [r + t for r, t in zip(rho, tau)]
    
    # Normalize so that the probabilities sum to 1.
    total = sum(combined)
    mu = [x / total for x in combined]
    
    return mu


def choose_degree(K):
    pdf = robust_soliton_distribution(K)
    # Create a list of degrees [1, 2, ..., K]
    degrees = list(range(1, K + 1))
    # Use random.choices to select one degree according to the distribution pdf.
    return random.choices(degrees, weights=pdf, k=1)[0]


def fountain_encoder(data: bytes, block_size: int):
    K = math.ceil(len(data) / block_size) # small block size
    blocks = [data[i * block_size:(i + 1) * block_size] for i in range(K)]

    while True:
        d = choose_degree(K)
        indices = random.sample(range(K), d)
        
        # XOR the selected blocks
        packet = blocks[indices[0]].ljust(block_size, b'\x00')
        for idx in indices[1:]:
            block = blocks[idx].ljust(block_size, b'\x00')
            packet = bytes(a ^ b for a, b in zip(packet, block))
        
        yield indices, packet


# alternative bitmask encoding (for reference)
def encode_packet_with_bitmask(indices, packet, K):
    bitmask = bytearray(math.ceil(K / 8))
    for i in indices:
        bitmask[i // 8] |= 1 << (i % 8)
    bitmask.reverse()
    payload = bytes(bitmask) + packet
    return base64.b64encode(payload).decode('utf-8')


def make_qr(data: str):
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

def prepare(file_path, block_size):
    # --- MODIFIED: file handling ---
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        raw = f.read()

    # --- MODIFIED: explicit protocol params ---
    filesize = len(raw)
    K = math.ceil(filesize / block_size)

    # --- MODIFIED: human-readable header ---
    meta_str = f"HEADER:{filename}:{filesize}:{K}:{block_size}"
    header_qr = make_qr(meta_str)

    # --- MODIFIED: encoder uses raw bytes ---
    encoder = fountain_encoder(raw, block_size)

    # --- MODIFIED: return FULL state ---
    state = {
        "encoder": encoder,
        "filesize": filesize,
        "K": K,
        "block_size": block_size,
        "filename": filename,
    }

    return header_qr, state


def stream_packets(state, running, rate):
    # Guard: stream_packets is called periodically even before Start is clicked
    if not running or state is None:
        return None

    encoder = state["encoder"]
    filesize = state["filesize"]
    K = state["K"]
    block_size = state["block_size"]

    update_interval = 1.0 / rate

    indices, packet = next(encoder)
    print(indices)
    b64 = encode_packet_with_bitmask(indices, packet, K)
    qr_img = make_qr(b64)
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
            block_size = gr.Slider(100, 1500, value=1500, step=50, label="Block size (bytes)")
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
