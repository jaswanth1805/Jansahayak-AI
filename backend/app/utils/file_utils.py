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


async def save_upload(file: UploadFile, upload_dir: str, document_id: str) -> str:
    """Save an incoming FastAPI UploadFile to the specified directory.
    
    Args:
        file: FastAPI UploadFile object.
        upload_dir: Destination folder path.
        
    Returns:
        The full destination file path.
    """
    settings = get_settings()
    validate_upload(file.filename or "", 0)
    os.makedirs(upload_dir, exist_ok=True)
    from app.services.document_registry import document_file_path
    destination_path = str(document_file_path(document_id))
    total_size = 0
    try:
        with open(destination_path, "xb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.max_upload_size_bytes:
                    raise HTTPException(status_code=413, detail="Uploaded file exceeds configured size limit.")
                buffer.write(chunk)
        if total_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        logger.info("Saved uploaded PDF (%d bytes)", total_size)
        return destination_path
    except Exception:
        try:
            os.remove(destination_path)
        except FileNotFoundError:
            pass
        raise


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text from a PDF document using PyMuPDF (fitz) with OCR fallback.
    
    Args:
        file_path: Path to the target PDF file.
        
    Returns:
        Dict containing:
            - pages: List of {"page_num": int, "text": str, "has_images": bool}
            - total_pages: Total page count
            - total_chars: Total character count extracted
            - is_scanned: True if document contains images but lacks machine text
            - extraction_method: 'direct_text', 'ocr', 'scanned_image', or 'empty'
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")
        
    import fitz  # PyMuPDF
    
    pages_data: List[Dict[str, Any]] = []
    used_ocr = False
    total_chars = 0
    has_any_images = False
    
    try:
        doc = fitz.open(file_path)
    except Exception as err:
        logger.error("Failed to open or parse PDF file %s: %s", file_path, err)
        raise ValueError(f"Corrupted or invalid PDF file: {err}") from err
        
    total_pages = len(doc)
    max_pages = get_settings().MAX_PDF_PAGES
    if total_pages > max_pages:
        doc.close()
        raise HTTPException(status_code=413, detail=f"PDF page count exceeds limit ({max_pages}).")
    
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]
        extracted_text = page.get_text("text").strip()
        image_list = page.get_images(full=True)
        has_images = len(image_list) > 0
        if has_images:
            has_any_images = True
        
        # If text is empty or sparse (<40 chars) and page has images, try OCR fallback
        if len(extracted_text) < 40 and has_images:
            logger.info("Page %d has minimal text (%d chars) but contains images. Attempting OCR fallback.", page_num, len(extracted_text))
            ocr_text = _run_page_ocr(page)
            if ocr_text and len(ocr_text) > len(extracted_text):
                extracted_text = ocr_text
                used_ocr = True
            
        total_chars += len(extracted_text)
        if total_chars > get_settings().MAX_EXTRACTED_TEXT_CHARS:
            doc.close()
            raise HTTPException(status_code=413, detail="Extracted PDF text exceeds configured size limit.")
        pages_data.append({
            "page_num": page_num,
            "text": extracted_text,
            "has_images": has_images,
        })
        
    doc.close()
    
    is_scanned = (total_chars < 30 and has_any_images)
    
    if used_ocr and total_chars >= 30:
        method = "ocr"
    elif is_scanned:
        method = "scanned_image"
    elif total_chars >= 30:
        method = "direct_text"
    else:
        method = "empty"
        
    return {
        "pages": pages_data,
        "total_pages": total_pages,
        "total_chars": total_chars,
        "is_scanned": is_scanned,
        "extraction_method": method,
    }


def _run_page_ocr(page) -> str:
    """Render page as image and run pytesseract OCR if local tesseract binary exists.
    
    Returns extracted text string, or empty string on failure.
    """
    try:
        import pytesseract
        from PIL import Image
        
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        
        for languages in ("eng+hin+tel", "eng+tel", "eng+hin", "eng"):
            try:
                text = pytesseract.image_to_string(image, lang=languages)
                if text.strip():
                    return text.strip()
            except Exception:
                continue
        return ""
    except Exception as ocr_err:
        logger.info("Local pytesseract OCR not active or executable missing: %s", ocr_err)
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
    try:
        from app.services.document_registry import registered_document_ids
        registered_ids = registered_document_ids()
    except Exception:
        registered_ids = None
    
    for filename in os.listdir(upload_dir):
        if filename.startswith("."):
            continue
        file_path = os.path.join(upload_dir, filename)
        if filename.lower().endswith(".pdf") and (
            registered_ids is None or filename[:-4] in registered_ids
        ):
            continue
        if os.path.isfile(file_path):
            try:
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    removed_count += 1
            except Exception as err:
                logger.warning("Could not delete old file %s: %s", file_path, err)
                
    return removed_count
