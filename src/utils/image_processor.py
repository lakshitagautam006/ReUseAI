"""Image processing utilities for ReUseAI.
Uses Pillow (PIL) only to handle validation, EXIF correction, color normalisation,
aspect-ratio preserving resizing, and Gemini Vision API preparation.
"""

from io import BytesIO
from typing import Tuple, Dict, Any, Union, Optional
from PIL import Image, ImageOps

from src.config import MAX_IMAGE_DIMENSION, SUPPORTED_IMAGE_TYPES, MAX_FILE_SIZE_MB

# Valid image formats recognized by Pillow
ALLOWED_PIL_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}


def _extract_raw_bytes(image_input: Any) -> Tuple[Optional[bytes], Optional[str]]:
    """Helper to extract raw bytes from bytes, BytesIO, or file-like streams.

    Returns:
        Tuple of (raw_bytes, error_message). If successful, error_message is None.
    """
    if image_input is None:
        return None, "No image provided. Please upload an image file."

    if isinstance(image_input, (bytes, bytearray)):
        return bytes(image_input), None

    if hasattr(image_input, "getvalue") and callable(image_input.getvalue):
        try:
            return image_input.getvalue(), None
        except Exception as exc:
            return None, f"Failed to read image buffer: {str(exc)}"

    if hasattr(image_input, "read") and callable(image_input.read):
        try:
            pos = image_input.tell() if hasattr(image_input, "tell") else 0
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            data = image_input.read()
            if hasattr(image_input, "seek"):
                image_input.seek(pos)
            return data, None
        except Exception as exc:
            return None, f"Failed to read image stream: {str(exc)}"

    return None, f"Unsupported input type '{type(image_input).__name__}'. Expected bytes, file stream, or PIL Image."


def validate_image(
    image_input: Union[bytes, bytearray, BytesIO, Image.Image, Any],
    max_file_size_mb: int = MAX_FILE_SIZE_MB,
) -> Tuple[bool, str]:
    """Validate that the input is a supported, non-empty, and uncorrupted image.

    Requirements:
    - Accepts JPG, JPEG, PNG, and WEBP.
    - Rejects unsupported formats (e.g. BMP, GIF, TIFF, SVG, PDF, or non-images).
    - Enforces max_file_size_mb (default 10 MB).
    - Handles empty (0-byte), corrupted, or truncated image uploads gracefully.

    Args:
        image_input: Raw image bytes, BytesIO buffer, Streamlit UploadedFile, or PIL Image.
        max_file_size_mb: Max allowed file size in megabytes.

    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    if image_input is None:
        return False, "No image provided. Please upload an image file."

    # Case 1: In-memory PIL Image instance
    if isinstance(image_input, Image.Image):
        w, h = image_input.size
        if w <= 0 or h <= 0:
            return False, "Invalid image dimensions (0 pixels)."

        fmt = getattr(image_input, "format", None)
        if fmt is not None:
            fmt_upper = str(fmt).upper()
            if fmt_upper not in ALLOWED_PIL_FORMATS:
                return (
                    False,
                    f"Unsupported image format: '{fmt_upper}'. Supported formats are JPG, JPEG, PNG, and WEBP.",
                )

        try:
            image_input.load()
            return True, ""
        except Exception as exc:
            return False, f"Corrupted or invalid image data: {str(exc)}"

    # Case 2: File-like object, BytesIO, or raw bytes
    raw_bytes, extract_err = _extract_raw_bytes(image_input)
    if extract_err:
        return False, extract_err

    if raw_bytes is None or len(raw_bytes) == 0:
        return False, "The uploaded image file is empty (0 bytes). Please upload a valid image."

    # Enforce file size limit
    max_bytes = max_file_size_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        file_size_mb = len(raw_bytes) / (1024 * 1024)
        return (
            False,
            f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed limit of {max_file_size_mb} MB.",
        )

    # Open with Pillow and verify format and integrity
    try:
        with Image.open(BytesIO(raw_bytes)) as img:
            detected_format = (img.format or "").upper()
            if not detected_format:
                return (
                    False,
                    "Unable to identify image format. Supported formats are JPG, JPEG, PNG, and WEBP.",
                )

            if detected_format not in ALLOWED_PIL_FORMATS:
                return (
                    False,
                    f"Unsupported image format: '{detected_format}'. Supported formats are JPG, JPEG, PNG, and WEBP.",
                )

            # Test full pixel decode to catch truncated or corrupted files
            img.load()

        return True, ""
    except Image.UnidentifiedImageError:
        return (
            False,
            "Invalid or unrecognized image file. Please upload a valid JPG, JPEG, PNG, or WEBP image.",
        )
    except (OSError, SyntaxError, ValueError) as exc:
        return False, f"Corrupted or damaged image file: {str(exc)}"
    except Exception as exc:
        return False, f"Image validation error: {str(exc)}"


def open_image(
    image_input: Union[bytes, bytearray, BytesIO, Image.Image, Any]
) -> Image.Image:
    """Safely open any supported image input into a loaded PIL Image.

    Args:
        image_input: Raw image bytes, BytesIO buffer, or PIL Image.

    Returns:
        Loaded PIL Image.

    Raises:
        ValueError: If the image cannot be read or validated.
    """
    if isinstance(image_input, Image.Image):
        image_input.load()
        return image_input

    raw_bytes, err = _extract_raw_bytes(image_input)
    if err or not raw_bytes:
        raise ValueError(err or "Empty image input.")

    bio = BytesIO(raw_bytes)
    img = Image.open(bio)
    img.load()
    return img


def preprocess_image(
    image: Image.Image,
    max_dim: int = MAX_IMAGE_DIMENSION,
) -> Image.Image:
    """Normalize and optimize an image for vision AI analysis.

    Processing steps:
    1. EXIF orientation correction: Auto-rotates image according to EXIF metadata
       and resets orientation tag to prevent double-rotation.
    2. RGB mode normalization:
       - Composites transparent channels (RGBA, LA, P) over a clean white background
         to avoid black background artifacts on transparent waste objects.
       - Converts Grayscale (L), CMYK, or 1-bit images to standard 3-channel RGB.
    3. Aspect-ratio preserving resize:
       - Resizes only when width or height exceeds `max_dim` (1024px).
       - Never upscales or resamples images that are within `max_dim`, preserving
         original sharpness and avoiding unnecessary compression artifacts.
       - Uses Lanczos filter (Image.Resampling.LANCZOS) for high-fidelity downscaling.

    Args:
        image: PIL Image instance.
        max_dim: Maximum allowed width or height in pixels (default 1024).

    Returns:
        Preprocessed RGB PIL Image suitable for Gemini Vision API.
    """
    # Step 1: Auto-correct EXIF orientation
    try:
        transposed = ImageOps.exif_transpose(image)
        processed = transposed if transposed is not None else image.copy()
    except Exception:
        processed = image.copy()

    # Step 2: Convert to RGB color mode with transparency compositing
    if processed.mode in ("RGBA", "LA"):
        rgba = processed if processed.mode == "RGBA" else processed.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        processed = background
    elif processed.mode == "P":
        # Palette mode with or without transparency
        rgba = processed.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        processed = background
    elif processed.mode != "RGB":
        processed = processed.convert("RGB")

    # Step 3: Resize only when exceeding max_dim, preserving exact aspect ratio
    w, h = processed.size
    if max(w, h) > max_dim:
        scale_ratio = max_dim / float(max(w, h))
        new_w = max(1, int(round(w * scale_ratio)))
        new_h = max(1, int(round(h * scale_ratio)))
        processed = processed.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return processed


def process_uploaded_image(
    image_input: Union[bytes, bytearray, BytesIO, Image.Image, Any],
    max_dim: int = MAX_IMAGE_DIMENSION,
    max_file_size_mb: int = MAX_FILE_SIZE_MB,
) -> Tuple[Optional[Image.Image], Optional[Image.Image], Dict[str, Any], Optional[str]]:
    """High-level pipeline: validates, opens original, and returns preprocessed image.

    Args:
        image_input: Uploaded file, bytes, or BytesIO buffer.
        max_dim: Max bounding box dimension (default 1024).
        max_file_size_mb: Max allowed file size in MB.

    Returns:
        Tuple of (preprocessed_img, original_img, metadata_dict, error_msg).
        If validation fails, preprocessed_img and original_img will be None,
        metadata_dict will be empty, and error_msg will contain the explanation.
    """
    is_valid, error_msg = validate_image(image_input, max_file_size_mb=max_file_size_mb)
    if not is_valid:
        return None, None, {}, error_msg

    try:
        original = open_image(image_input)
        metadata = get_image_metadata(original)
        preprocessed = preprocess_image(original, max_dim=max_dim)
        metadata["preprocessed_width"] = preprocessed.width
        metadata["preprocessed_height"] = preprocessed.height
        metadata["is_resized"] = original.size != preprocessed.size
        return preprocessed, original, metadata, None
    except Exception as exc:
        return None, None, {}, f"Image processing failed: {str(exc)}"


def image_to_bytes(
    image: Image.Image,
    format_name: str = "JPEG",
    quality: int = 90,
) -> bytes:
    """Serialize a PIL Image into a byte buffer for API transmission or export.

    Args:
        image: PIL Image instance.
        format_name: Output format ("JPEG", "PNG", "WEBP").
        quality: Compression quality (1-100) for JPEG and WEBP.

    Returns:
        Raw bytes.
    """
    buffer = BytesIO()
    save_format = format_name.upper()

    if save_format in ("JPG", "JPEG"):
        save_format = "JPEG"
        image.save(buffer, format=save_format, quality=quality, optimize=True)
    elif save_format == "WEBP":
        image.save(buffer, format="WEBP", quality=quality)
    elif save_format == "PNG":
        image.save(buffer, format="PNG", optimize=True)
    else:
        image.save(buffer, format=save_format)

    return buffer.getvalue()


def get_image_metadata(
    image: Image.Image,
    raw_bytes_len: Optional[int] = None,
) -> Dict[str, Any]:
    """Extract key dimensional, format, and resolution metadata from a PIL Image.

    Args:
        image: PIL Image instance.
        raw_bytes_len: Optional size in bytes if available from upload.

    Returns:
        Dictionary of image properties.
    """
    w, h = image.size
    aspect_ratio = round(w / h, 2) if h > 0 else 1.0
    megapixels = round((w * h) / 1_000_000, 2)
    fmt = getattr(image, "format", "RGB") or "RGB"

    meta: Dict[str, Any] = {
        "width": w,
        "height": h,
        "aspect_ratio": f"{aspect_ratio}:1",
        "megapixels": megapixels,
        "mode": image.mode,
        "format": str(fmt).upper(),
    }

    if raw_bytes_len is not None:
        meta["file_size_bytes"] = raw_bytes_len
        meta["file_size_kb"] = round(raw_bytes_len / 1024, 1)
        meta["file_size_mb"] = round(raw_bytes_len / (1024 * 1024), 2)

    return meta
