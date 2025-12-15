# Gradio-based UI
# Focus: cleaner layout, better state handling, start/stop control, and stability

import gradio as gr
import qrcode
import base64
import math
import random
import time
from typing import Generator, Tuple, List

# ---------------- Core logic ----------------

MAX_QR_PAYLOAD_SIZE = 2210  # bytes


def robust_soliton_distribution(N, c=0.1, delta=0.5):
    R = c * math.log(N / delta) * math.sqrt(N)
    tau = [0.0] * (N + 1)
    for i in range(1, int(N / R)):
        tau[i] = R / (i * N)
    tau[int(N / R)] = R * math.log(R / delta) / N

    rho = [0.0] * (N + 1)
    rho[1] = 1 / N
    for i in range(2, N + 1):
        rho[i] = 1 / (i * (i - 1))

    Z = sum(rho[1:]) + sum(tau[1:])
    mu = [(rho[i] + tau[i]) / Z for i in range(N + 1)]
    return mu


def sample_degree(mu):
    r = random.random()
    s = 0.0
    for i in range(1, len(mu)):
        s += mu[i]
        if r <= s:
            return i
    return len(mu) - 1


def fountain_encoder(data: bytes, chunk_size: int) -> Generator[Tuple[List[int], bytes], None, None]:
    K = math.ceil(len(data) / chunk_size)
    chunks = [data[i * chunk_size:(i + 1) * chunk_size] for i in range(K)]
    mu = robust_soliton_distribution(K)

    while True:
        d = sample_degree(mu)
        indices = random.sample(range(K), d)
        packet = bytearray(chunk_size)
        for i in indices:
            chunk = chunks[i]
            for j in range(len(chunk)):
                packet[j] ^= chunk[j]
        yield indices, bytes(packet)


def encode_packet_with_bitmask(filesize, indices, packet, K):
    bitmask = bytearray(math.ceil(K / 8))
    for i in indices:
        bitmask[i // 8] |= 1 << (i % 8)

    header = filesize.to_bytes(4, 'big') + K.to_bytes(2, 'big')
    payload = header + bytes(bitmask) + packet
    return base64.b64encode(payload).decode()


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


def prepare(file, chunk_size):
    raw = file
    filesize = len(raw)
    K = math.ceil(filesize / chunk_size)

    header_payload = base64.b64encode(filesize.to_bytes(4, 'big') + K.to_bytes(2, 'big')).decode()
    header_qr = make_qr(header_payload)

    encoder = fountain_encoder(raw, chunk_size)
    return header_qr, encoder, filesize, K


def stream_packets(state, running, rate):
    # Guard: stream_packets is called periodically even before Start is clicked
    if not running or state is None:
        return None

    encoder, filesize, K = state
    update_interval = 1.0 / rate

    indices, packet = next(encoder)
    b64 = encode_packet_with_bitmask(filesize, indices, packet, K)
    qr_img = make_qr(b64)
    time.sleep(update_interval)
    return qr_img


# ---------------- UI definition ----------------

with gr.Blocks(title="LT Codes Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 📡 LT Codes Generator
    Upload a file and continuously generate QR packets.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Input File", type="binary")
            chunk_size = gr.Slider(100, 1500, value=800, step=50, label="Chunk size (bytes)")
            rate = gr.Slider(0.2, 5.0, value=1.0, step=0.2, label="QRs per second")
            start_btn = gr.Button("▶ Start", variant="primary")
            stop_btn = gr.Button("⏹ Stop", variant="secondary")
        with gr.Column(scale=1):
            header_qr = gr.Image(label="Header QR", type="pil")
            packet_qr = gr.Image(label="Packet QR", type="pil")

    state = gr.State()
    running = gr.State(False)

    def on_start(file, chunk_size, rate):
        header, encoder, filesize, K = prepare(file, chunk_size)
        return header, (encoder, filesize, K), True # [header_qr, state, running]
    
    def on_stop():
        return False, None, None # [running, header_qr, packet_qr]

    start_btn.click(
        fn=on_start,
        inputs=[file_input, chunk_size, rate],
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
