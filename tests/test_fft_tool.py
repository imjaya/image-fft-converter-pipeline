# -*- coding: utf-8 -*-
"""Unit tests for the FFT computation tool (fft_tool.py)."""

from pathlib import Path

import numpy as np
from PIL import Image

from fft_tool import compute_fft


def test_compute_fft(tmp_path: Path) -> None:
    """compute_fft creates an output file for a small image."""
    # Create a small 4x4 grayscale image
    arr = np.arange(16, dtype=np.uint8).reshape(4, 4)
    input_file = tmp_path / "in.png"
    output_file = tmp_path / "out.png"
    Image.fromarray(arr).save(input_file)

    compute_fft(str(input_file), str(output_file))

    assert output_file.exists()
    out_img = Image.open(output_file)
    assert out_img.size == (4, 4)
