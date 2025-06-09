# -*- coding: utf-8 -*-
"""Utility for converting images into their FFT magnitude representation."""

import argparse

import numpy as np
from PIL import Image


def compute_fft(input_path: str, output_path: str) -> None:
    """Compute and save the magnitude of the 2-D FFT of ``input_path``.

    Args:
        input_path: Path to the grayscale PNG image to process.
        output_path: Path where the resulting FFT magnitude image
            will be stored.

    """
    # Load image in grayscale mode and convert to a NumPy array
    img = Image.open(input_path).convert("L")
    arr = np.array(img)

    # Perform 2D FFT and shift zero frequency to the center
    fft = np.fft.fftshift(np.fft.fft2(arr))
    magnitude = np.abs(fft)

    # Use log scaling to make visualization easier
    magnitude = np.log1p(magnitude)

    # Normalize the result into 0-255 range for image output
    magnitude -= magnitude.min()
    magnitude /= magnitude.max()
    magnitude *= 255.0

    # Save back to PNG
    result = Image.fromarray(magnitude.astype(np.uint8))
    result.save(output_path)


def main() -> None:
    """Parse command-line arguments and run :func:`compute_fft`."""
    parser = argparse.ArgumentParser(
        description="Compute 2D FFT of a grayscale PNG"
    )
    parser.add_argument("input", help="input PNG file")
    parser.add_argument("output", help="output PNG file")
    args = parser.parse_args()
    compute_fft(args.input, args.output)


if __name__ == "__main__":
    main()
