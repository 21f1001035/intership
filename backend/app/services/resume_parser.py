from __future__ import annotations

import io
import structlog
from uuid import UUID

from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.models.resume_extraction import ResumeExtraction
from app.core.config import settings

logger = structlog.get_logger(__name__)


class ResumeParserService:
    """
    Handles PDF text extraction and LLM-based resume normalisation.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract plaintext from a PDF byte buffer.
        Tries pdfplumber first; falls back to PyPDF2 if it fails.
        """
        text = self._extract_with_pdfplumber(file_bytes)
        if text and len(text.strip()) > 50:
            return text

        logger.warning("pdfplumber extraction returned sparse text, trying PyPDF2")
        fallback = self._extract_with_pypdf2(file_bytes)
        return fallback if fallback else (text or "")

    def _extract_with_pdfplumber(self, file_bytes: bytes) -> str:
        try:
            import pdfplumber  # noqa: PLC0415

            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                return "\n".join(pages_text)
        except Exception as exc:
            logger.warning("pdfplumber failed", exc_info=exc)
            return ""

    def _extract_with_pypdf2(self, file_bytes: bytes) -> str:
        try:
            import PyPDF2  # noqa: PLC0415

            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            return "\n".join(pages_text)
        except Exception as exc:
            logger.warning("PyPDF2 fallback also failed", exc_info=exc)
            return ""

    # ------------------------------------------------------------------
    # Full parse pipeline
    # ------------------------------------------------------------------

    def parse_resume(
        self,
        application_id: UUID,
        file_bytes: bytes,
        db: Session,
    ) -> ResumeExtraction:
        """
        Full resume parsing pipeline:
        1. Extract raw text from the PDF.
        2. Call the LLM to normalise into structured data.
        3. Upsert a ResumeExtraction record in the database.

        Returns:
            The saved ResumeExtraction ORM instance.
        """
        logger.info("Starting resume parse", application_id=str(application_id))

        # Step 1: extract text
        raw_text = self.extract_text_from_pdf(file_bytes)
        if not raw_text or not raw_text.strip():
            logger.warning(
                "No text could be extracted from PDF",
                application_id=str(application_id),
            )
            raw_text = ""

        # Step 2: LLM normalisation
        structured_profile = None
        structured_dict: dict = {}
        extraction_provider = "openai"
        extraction_model = settings.OPENAI_MODEL
        confidence = None

        if raw_text.strip():
            try:
                structured_profile = self._llm.normalize_resume(raw_text)
                structured_dict = structured_profile.model_dump()
                confidence = 0.9  # heuristic; could be refined
            except Exception as exc:
                logger.error(
                    "LLM resume normalisation failed",
                    application_id=str(application_id),
                    exc_info=exc,
                )
                extraction_provider = "failed"
                extraction_model = None
                confidence = 0.0

        # Step 3: upsert ResumeExtraction
        extraction = (
            db.query(ResumeExtraction)
            .filter(ResumeExtraction.application_id == application_id)
            .first()
        )
        if extraction is None:
            extraction = ResumeExtraction(application_id=application_id)
            db.add(extraction)

        extraction.raw_text = raw_text
        extraction.structured_json = structured_dict
        extraction.extraction_provider = extraction_provider
        extraction.extraction_model = extraction_model
        extraction.extraction_version = "1.0"
        extraction.confidence_score = confidence

        db.flush()
        logger.info(
            "Resume extraction saved",
            application_id=str(application_id),
            has_structured=bool(structured_dict),
        )
        return extraction
