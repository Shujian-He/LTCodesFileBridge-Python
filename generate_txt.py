import sys

byte_count = 500000

def generate_file(byte_count, filename="output.txt"):
    # The pattern used for each "byte"
    pattern = "abcdefg "  # 8 bytes in ASCII encoding
    # Repeat the pattern enough times and slice to match byte_count
    content = (pattern * ((byte_count // len(pattern)) + 1))[:byte_count]
    
    with open(filename, "w") as file:
        file.write(content)
    print(f"Generated file '{filename}' with {byte_count} bytes.")


generate_file(byte_count)