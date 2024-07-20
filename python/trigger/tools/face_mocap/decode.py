"""Python module responsible for decoding the mov files."""

import shutil
from pathlib import Path
import subprocess
import logging

LOG = logging.getLogger(__name__)

# find the ffmpeg.exe file in the current directory
ffmpeg_path = Path(__file__).parent / "ffmpeg.exe"

if not ffmpeg_path.exists():
    raise FileNotFoundError("ffmpeg.exe not found in the current directory.")

def extract_wav(mov_file_path, output_file=None, overwrite=False):
    """Split a wav file from a mov file.

    Args:
        mov_file_path (str): Path to the mov file.
        output_file (str): Path to the output wav file.
        overwrite (bool): Overwrite the file if it already exists
    """
    # if the output file is not specified, use the mov file name and export
    # it to the same directory
    output_path = output_file or Path(mov_file_path).with_suffix(".wav").as_posix()

    if Path(output_path).exists():
        if not overwrite:
            LOG.warning("Output file already exists. Set overwrite to True to overwrite the file. Skipping wav extraction.")
            return output_path
        else:
            Path(output_path).unlink()
    flags = [
        ffmpeg_path.as_posix(),
        "-i",
        mov_file_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        output_path
    ]

    subprocess.check_call(flags, shell=False)
    return output_path

def extract_jpg(mov_file_path, output_folder=None, overwrite=False):
    """Extract the jpg files from a mov file.

    Args:
        mov_file_path (str): Path to the mov file.
        output_folder (str): Path to the output folder.
        overwrite (bool): Overwrite the files if they already exist.
    """

    output_folder = output_folder or (Path(mov_file_path).parent / "jpgs").as_posix()

    output_file_name = str(Path(mov_file_path).stem)

    if Path(output_folder).exists() and list(Path(output_folder).rglob("*.jpg")):
        if not overwrite:
            LOG.warning("Output file already exists. Set overwrite to True to overwrite the file. Skipping jpg extraction.")
            return output_folder
        else:
            shutil.rmtree(output_folder)

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    flags = [
        ffmpeg_path.as_posix(),
        "-i",
        mov_file_path,
        "-q:v",
        "2",
        f"{output_folder}\\{output_file_name}_%06d.jpg"
    ]

    subprocess.check_call(flags, shell=False)
    return output_folder




