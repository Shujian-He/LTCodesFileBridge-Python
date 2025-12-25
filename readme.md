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

- **prototype.py**: Prototype implementation of LT codes algorithm
- **readcodes_zbar.py**: Module for reading QR codes using the pyzbar library
- **showcodes_header.py**: Script to generate and display header QR codes
- **simulate_decode.py**: Simulation script for testing the decoding process
- **generate_txt.py**: Script for generating sample text files for testing
- **tools.py**: Utility functions and helper tools for the project
- **ui_gradio.py**: Gradio-based web user interface for interactive file encoding/decoding
- **readme.md**: This README file with project documentation
- **requirements.txt**: List of Python dependencies required for the project
- **LICENSE**: MIT License file

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