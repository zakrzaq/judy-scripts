import subprocess
import platform
import os
import argparse


def detect_gpu_vendor():
    """
    Detects the GPU vendor on the system and returns a string: 'nvidia', 'amd', 'apple', or None.
    """
    system = platform.system()

    if system == "Linux":
        result = subprocess.run(["lspci"], stdout=subprocess.PIPE)
        output = result.stdout.decode().lower()
        if "nvidia" in output:
            return "nvidia"
        elif "amd" in output or "radeon" in output:
            return "amd"
    elif system == "Windows":
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            stdout=subprocess.PIPE,
        )
        output = result.stdout.decode().lower()
        if "nvidia" in output:
            return "nvidia"
        elif "amd" in output or "radeon" in output:
            return "amd"
    elif system == "Darwin":  # macOS
        result = subprocess.run(
            ["sysctl", "machdep.cpu.brand_string"], stdout=subprocess.PIPE
        )
        output = result.stdout.decode().lower()
        if (
            "apple" in output or "m1" in output or "m2" in output
        ):  # Detect Apple Silicon
            return "apple"
        elif "amd" in output or "radeon" in output:
            return "amd"
        elif "nvidia" in output:
            return "nvidia"

    return None


def convert_h265_to_h264(input_file, output_file):
    """
    Converts an input H.265 video file to H.264 format using the appropriate hardware codec if available.
    """
    gpu_vendor = detect_gpu_vendor()

    if gpu_vendor == "nvidia":
        codec = "h264_nvenc"
    elif gpu_vendor == "amd":
        codec = "h264_amf"
    elif gpu_vendor == "apple":
        codec = "h264_videotoolbox"
    else:
        codec = "libx264"

    command = [
        "ffmpeg",
        "-hwaccel",
        "auto",
        "-i",
        input_file,
        "-c:v",
        codec,
        "-preset",
        "slow",
        "-crf",
        "23",
        "-c:a",
        "copy",
        output_file,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Conversion complete: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during conversion of {input_file}: {e}")


def process_all_mov_files(input_dir, output_dir, diff=False):
    """
    Processes all .mov files in the input directory. If `diff` is True, only files not already in the output directory
    will be processed. Existing .mp4 files will be skipped.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mov_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".mov")]

    if diff:
        # Filter out files that already exist in the output directory as .mp4
        mov_files = [
            f for f in mov_files if not os.path.exists(os.path.join(output_dir, f.lower().replace(".mov", ".mp4")))
        ]

    for idx, file_name in enumerate(mov_files, start=1):
        input_file = os.path.join(input_dir, file_name)
        output_file = os.path.join(
            output_dir, file_name.lower().replace(".mov", ".mp4")
        )  # Change extension to .mp4

        # Skip files if the output .mp4 file already exists
        if os.path.exists(output_file):
            print(f"File already exists, skipping: {output_file}")
            continue

        print(f"Processing file {idx}/{len(mov_files)}: {input_file}")
        try:
            convert_h265_to_h264(input_file, output_file)
        except Exception as e:
            print(f"Failed to convert {input_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="A script to handle video conversion."
    )
    parser.add_argument(
        "operation",
        choices=["convert", "convert-diff"],
        help="Operation to perform: 'convert' to convert all MOV files, or 'convert-diff' to convert only files not in the output directory.",
    )
    parser.add_argument(
        "input_directory", help="Path to the input directory containing MOV files."
    )
    parser.add_argument(
        "output_directory",
        help="Path to the output directory where results will be saved.",
    )

    args = parser.parse_args()

    input_directory = args.input_directory
    output_directory = args.output_directory

    if args.operation == "convert-diff":
        process_all_mov_files(input_directory, output_directory, diff=True)
    elif args.operation == "convert":
        process_all_mov_files(input_directory, output_directory, diff=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()