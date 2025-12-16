# LTCodesFileBridge-Python

A Python implementation of LT Codes for reliable file transmission over QR codes. This project allows you to encode files into a stream of QR codes using fountain codes, which can be scanned and decoded even if some packets are lost or corrupted.

## Features

- **LT Encoding/Decoding**: Implements LT codes with robust Soliton distribution for efficient fountain coding.
- **QR Code Generation**: Converts encoded packets into QR codes for easy transmission.
- **File Reconstruction**: Decodes received QR packets back into the original file.
- **Web UI**: Provides Gradio web interfaces for interactive use.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/shujian-he/LTCodesFileBridge-Python.git
   cd LTCodesFileBridge-Python
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Note: Ensure you have Python 3.7+ installed.

## Usage

### Gradio UI (Recommended)

Run the Gradio-based interface:
```bash
python ui_gradio.py
```

This launches a web interface where you can:
- Upload a file
- Adjust chunk size and QR generation rate
- Generate and display header and packet QR codes
- Start/Stop the streaming process

## How It Works

1. **Encoding**:
   - File is split into chunks
   - LT codes generate redundant packets by XORing random subsets of chunks
   - Each packet includes a bitmask indicating which chunks were used
   - Packets are encoded into QR codes

2. **Transmission**:
   - Display QR codes sequentially
   - Receiver scans QR codes (order doesn't matter)

3. **Decoding**:
   - Use peeling algorithm to recover original chunks
   - XOR operations reconstruct the original data

## Project Structure

- `encode_decode.py`: Core LT encoding and decoding logic
- `tools.py`: Robust Soliton distribution implementation
- `ui_gradio.py`: Gradio web interface
- `readcodes_zbar.py`: QR code reading functionality
- `showcodes_header.py`: QR generation and display
- `generate_txt.py`: Test file generation

## Dependencies

- Pillow: Image processing
- pyzbar: QR code decoding
- qrcode: QR code generation
- matplotlib: Plotting (for demos)
- gradio: Web UI framework

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## References

- Luby, M. (2002). LT codes. In Proceedings of the 43rd Annual IEEE Symposium on Foundations of Computer Science (pp. 271-280).