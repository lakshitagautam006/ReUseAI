"""Comprehensive test suite for Phase 3 Image Preprocessing in ReUseAI.
Tests format validation, corrupted/empty input handling, EXIF orientation correction,
RGB color space normalization, downscaling constraints, and aspect ratio preservation.
"""

import unittest
from io import BytesIO
from PIL import Image, ImageOps

from src.config import MAX_IMAGE_DIMENSION, MAX_FILE_SIZE_MB
from src.utils.image_processor import (
    validate_image,
    preprocess_image,
    image_to_bytes,
    get_image_metadata,
    open_image,
    process_uploaded_image,
)


class TestPhase3ImageProcessor(unittest.TestCase):
    """Unit tests fulfilling all Phase 3 requirements."""

    def setUp(self):
        # 1. Valid JPG image bytes
        img_jpg = Image.new("RGB", (640, 480), color=(100, 150, 200))
        buf_jpg = BytesIO()
        img_jpg.save(buf_jpg, format="JPEG")
        self.jpg_bytes = buf_jpg.getvalue()

        # 2. Valid PNG image bytes (with alpha channel)
        img_png = Image.new("RGBA", (500, 500), color=(50, 200, 50, 128))
        buf_png = BytesIO()
        img_png.save(buf_png, format="PNG")
        self.png_bytes = buf_png.getvalue()

        # 3. Valid WEBP image bytes
        img_webp = Image.new("RGB", (320, 240), color=(220, 180, 80))
        buf_webp = BytesIO()
        img_webp.save(buf_webp, format="WEBP")
        self.webp_bytes = buf_webp.getvalue()

    def test_valid_image_formats_jpg_png_webp(self):
        """Requirement 3 & 7: Test that JPG, PNG, and WEBP images pass validation."""
        for fmt_name, raw_bytes in [
            ("JPG", self.jpg_bytes),
            ("PNG", self.png_bytes),
            ("WEBP", self.webp_bytes),
        ]:
            with self.subTest(format=fmt_name):
                is_valid, err_msg = validate_image(raw_bytes)
                self.assertTrue(is_valid, f"{fmt_name} should be valid, but got: {err_msg}")
                self.assertEqual(err_msg, "")

    def test_image_larger_than_1024_resizes_and_preserves_aspect_ratio(self):
        """Requirement 4 & 7: Test that images exceeding MAX_IMAGE_DIMENSION (1024)
        are downscaled properly while preserving the exact aspect ratio.
        """
        # Test 1: Landscape image 2048 x 1024 (aspect ratio 2:1)
        large_landscape = Image.new("RGB", (2048, 1024), color=(30, 80, 120))
        processed_landscape = preprocess_image(large_landscape, max_dim=MAX_IMAGE_DIMENSION)

        self.assertEqual(processed_landscape.mode, "RGB")
        self.assertEqual(processed_landscape.width, 1024)
        self.assertEqual(processed_landscape.height, 512)
        # Verify 2:1 aspect ratio is preserved
        self.assertAlmostEqual(processed_landscape.width / processed_landscape.height, 2.0, places=2)

        # Test 2: Portrait image 1500 x 3000 (aspect ratio 1:2)
        large_portrait = Image.new("RGB", (1500, 3000), color=(180, 40, 40))
        processed_portrait = preprocess_image(large_portrait, max_dim=1024)

        self.assertEqual(processed_portrait.mode, "RGB")
        self.assertEqual(processed_portrait.height, 1024)
        self.assertEqual(processed_portrait.width, 512)
        self.assertAlmostEqual(processed_portrait.height / processed_portrait.width, 2.0, places=2)

    def test_image_within_1024_is_not_resized(self):
        """Requirement 4: Ensure images <= MAX_IMAGE_DIMENSION are not resized or resampled,
        preventing unnecessary image quality loss.
        """
        original = Image.new("RGB", (800, 600), color=(50, 120, 60))
        processed = preprocess_image(original, max_dim=1024)

        self.assertEqual(processed.size, (800, 600))
        self.assertEqual(processed.size, original.size)

    def test_corrupted_image_detection(self):
        """Requirement 3 & 7: Test that corrupted and truncated images are caught gracefully."""
        # Case A: Valid JPEG header but truncated stream halfway through
        truncated_bytes = self.jpg_bytes[: len(self.jpg_bytes) // 3]
        is_valid, err_msg = validate_image(truncated_bytes)
        self.assertFalse(is_valid)
        self.assertTrue(len(err_msg) > 0)
        self.assertTrue("corrupted" in err_msg.lower() or "damaged" in err_msg.lower() or "truncated" in err_msg.lower())

        # Case B: Random pseudo-image corrupted binary stream
        fake_corrupted = b"\xff\xd8\xff\xe0" + b"\x00" * 20 + b"RANDOM_CORRUPTED_GARBAGE" * 5
        is_valid2, err_msg2 = validate_image(fake_corrupted)
        self.assertFalse(is_valid2)
        self.assertTrue(len(err_msg2) > 0)

    def test_unsupported_formats_rejected(self):
        """Requirement 3 & 7: Test that unsupported formats (BMP, GIF, TIFF, text) are rejected."""
        # Case A: BMP image
        img_bmp = Image.new("RGB", (64, 64), color="red")
        buf_bmp = BytesIO()
        img_bmp.save(buf_bmp, format="BMP")
        is_valid_bmp, msg_bmp = validate_image(buf_bmp.getvalue())
        self.assertFalse(is_valid_bmp)
        self.assertIn("Unsupported image format", msg_bmp)
        self.assertIn("BMP", msg_bmp)

        # Case B: GIF image
        img_gif = Image.new("RGB", (64, 64), color="blue")
        buf_gif = BytesIO()
        img_gif.save(buf_gif, format="GIF")
        is_valid_gif, msg_gif = validate_image(buf_gif.getvalue())
        self.assertFalse(is_valid_gif)
        self.assertIn("Unsupported image format", msg_gif)
        self.assertIn("GIF", msg_gif)

        # Case C: Plain text or PDF file bytes
        is_valid_txt, msg_txt = validate_image(b"This is a plain text file, not an image.")
        self.assertFalse(is_valid_txt)
        self.assertTrue(len(msg_txt) > 0)

    def test_empty_image_upload_rejected(self):
        """Requirement 3: Test that empty (0-byte) image uploads are rejected gracefully."""
        is_valid_empty_bytes, msg_empty = validate_image(b"")
        self.assertFalse(is_valid_empty_bytes)
        self.assertIn("empty", msg_empty.lower())

        is_valid_empty_buffer, msg_buf = validate_image(BytesIO(b""))
        self.assertFalse(is_valid_empty_buffer)
        self.assertIn("empty", msg_buf.lower())

        is_valid_none, msg_none = validate_image(None)
        self.assertFalse(is_valid_none)
        self.assertIn("no image provided", msg_none.lower())

    def test_exceeding_max_file_size(self):
        """Requirement 3: Test that files exceeding MAX_FILE_SIZE_MB (10 MB) are rejected."""
        # Simulate oversized image by passing custom max_file_size_mb
        # For fast test execution, test with 1 MB limit against a 1.5 MB buffer
        oversized_data = b"0" * (2 * 1024 * 1024)  # 2 MB dummy bytes
        is_valid, msg = validate_image(oversized_data, max_file_size_mb=1)
        self.assertFalse(is_valid)
        self.assertIn("exceeds maximum allowed limit", msg)

    def test_exif_orientation_correction(self):
        """Requirement 4 & 7: Verify that EXIF orientation is handled correctly.
        Tag 0x0112 = 6 specifies a 90-degree clockwise rotation, transposing (w, h).
        """
        # Create a portrait image (width=100, height=250)
        img = Image.new("RGB", (100, 250), color=(10, 150, 80))
        exif = img.getexif()
        exif[0x0112] = 6  # Orientation 6: Rotate 90 CW (transposes width and height)

        buf = BytesIO()
        img.save(buf, format="JPEG", exif=exif)
        buf.seek(0)

        # Open raw image
        raw_loaded = Image.open(buf)
        self.assertEqual(raw_loaded.size, (100, 250))

        # Preprocess image
        processed = preprocess_image(raw_loaded)
        # Orientation 6 should rotate 90 CW: dimensions transpose to (250, 100)
        self.assertEqual(processed.size, (250, 100))
        self.assertEqual(processed.mode, "RGB")

    def test_transparency_compositing_rgba_to_rgb(self):
        """Requirement 4: Verify that RGBA transparent images are composited over a clean
        white background rather than turning black upon RGB conversion.
        """
        # Create image with completely transparent background (alpha=0)
        rgba_img = Image.new("RGBA", (100, 100), color=(0, 0, 0, 0))
        # Draw opaque green center (50, 50)
        rgba_img.putpixel((50, 50), (34, 139, 34, 255))

        processed = preprocess_image(rgba_img)
        self.assertEqual(processed.mode, "RGB")
        # Corner pixel should be composite white (255, 255, 255)
        self.assertEqual(processed.getpixel((0, 0)), (255, 255, 255))
        # Center pixel remains green
        self.assertEqual(processed.getpixel((50, 50)), (34, 139, 34))

    def test_palette_image_conversion(self):
        """Requirement 4: Verify Palette (mode P) images convert seamlessly to RGB."""
        p_img = Image.new("P", (80, 80))
        p_img.putpalette([200, 100, 50] * 256)
        processed = preprocess_image(p_img)
        self.assertEqual(processed.mode, "RGB")

    def test_process_uploaded_image_helper(self):
        """Requirement 6: Test the end-to-end process_uploaded_image helper pipeline."""
        prep_img, orig_img, meta, err = process_uploaded_image(self.jpg_bytes)
        self.assertIsNone(err)
        self.assertIsNotNone(prep_img)
        self.assertIsNotNone(orig_img)
        self.assertEqual(prep_img.mode, "RGB")
        self.assertIn("width", meta)
        self.assertIn("height", meta)
        self.assertIn("preprocessed_width", meta)
        self.assertIn("is_resized", meta)


if __name__ == "__main__":
    unittest.main()
