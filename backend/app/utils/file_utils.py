"""File Handling and PDF Extraction Utilities.

Provides secure PDF validation, PyMuPDF text extraction with OCR fallback,
and file management helpers.
"""

import io
import logging
import os
import time
from typing import Dict, Any, List
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def validate_upload(filename: str, file_size: int) -> None:
    """Validate uploaded file format and size limits.
    
    Args:
        filename: Name of the uploaded file.
        file_size: Size in bytes.
        
    Raises:
        HTTPException: If file is not a PDF or exceeds maximum upload limit.
    """
    settings = get_settings()
    
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents (.pdf) are supported for scheme analysis."
        )
        
    if file_size > settings.max_upload_size_bytes:
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {max_mb} MB."
        )


async def save_upload(file: UploadFile, upload_dir: str) -> str:
    """Save an incoming FastAPI UploadFile to the specified directory.
    
    Args:
        file: FastAPI UploadFile object.
        upload_dir: Destination folder path.
        
    Returns:
        The full destination file path.
    """
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = os.path.join(upload_dir, file.filename)
    
    # Avoid file collisions by prefixing or renaming if required
    base_name, ext = os.path.splitext(file.filename)
    counter = 1
    while os.path.exists(destination_path):
        destination_path = os.path.join(upload_dir, f"{base_name}_{counter}{ext}")
        counter += 1
        
    content = await file.read()
    with open(destination_path, "wb") as buffer:
        buffer.write(content)
        
    logger.info("Saved upload to %s (%d bytes)", destination_path, len(content))
    return destination_path


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text from a PDF document using PyMuPDF (fitz) with OCR fallback.
    
    Args:
        file_path: Path to the target PDF file.
        
    Returns:
        Dict containing:
            - pages: List of {"page_num": int, "text": str, "has_images": bool}
            - total_pages: Total page count
            - extraction_method: 'direct_text', 'ocr', or 'hybrid'
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")
        
    import fitz  # PyMuPDF
    
    pages_data: List[Dict[str, Any]] = []
    used_ocr = False
    used_direct = False
    
    try:
        doc = fitz.open(file_path)
    except Exception as err:
        logger.error("Failed to open or parse PDF file %s: %s", file_path, err)
        raise ValueError(f"Corrupted or invalid PDF file: {err}") from err
        
    total_pages = len(doc)
    
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]
        extracted_text = page.get_text("text").strip()
        image_list = page.get_images(full=True)
        has_images = len(image_list) > 0
        
        # If text is empty or sparse (<40 chars) and page has images, try OCR fallback
        if len(extracted_text) < 40 and has_images:
            logger.info("Page %d has minimal text but contains images. Attempting OCR fallback.", page_num)
            ocr_text = _run_page_ocr(page)
            if ocr_text:
                extracted_text = ocr_text
                used_ocr = True
            else:
                used_direct = True
        else:
            used_direct = True
            
        pages_data.append({
            "page_num": page_num,
            "text": extracted_text,
            "has_images": has_images,
        })
        
    doc.close()
    
    if used_ocr and used_direct:
        method = "hybrid"
    elif used_ocr:
        method = "ocr"
    else:
        method = "direct_text"
        
    return {
        "pages": pages_data,
        "total_pages": total_pages,
        "extraction_method": method,
    }


def _run_page_ocr(page) -> str:
    """Render page as image and run pytesseract OCR.
    
    Returns extracted text string, or empty string on failure.
    """
    try:
        import pytesseract
        from PIL import Image
        
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        
        # Run OCR with English and Hindi if available in tesseract
        try:
            text = pytesseract.image_to_string(image, lang="eng+hin")
        except Exception:
            text = pytesseract.image_to_string(image, lang="eng")
            
        return text.strip()
    except Exception as ocr_err:
        logger.warning("OCR processing failed for page: %s", ocr_err)
        return ""


def cleanup_old_files(upload_dir: str, max_age_hours: int = 24) -> int:
    """Remove files in directory older than max_age_hours.
    
    Args:
        upload_dir: Directory containing temporary files.
        max_age_hours: Threshold in hours.
        
    Returns:
        Number of removed files.
    """
    if not os.path.exists(upload_dir):
        return 0
        
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    removed_count = 0
    
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            try:
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    removed_count += 1
            except Exception as err:
                logger.warning("Could not delete old file %s: %s", file_path, err)
                
    return removed_count
