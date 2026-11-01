"""Data Transfer Objects and Pydantic Schemas.

This module defines all Pydantic request and response schemas for JanSahayak AI.
Schemas ensure strong data typing, validation, and automated OpenAPI documentation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Language(str, Enum):
    """Supported languages in JanSahayak AI.
    
    'en': English
    'hi': Hindi (हिंदी)
    'te': Telugu (తెలుగు)
    """
    ENGLISH = "en"
    HINDI = "hi"
    TELUGU = "te"


class ChatMessage(BaseModel):
    """A single turn in a multi-turn conversation history."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="The message content text")
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the message was sent or received"
    )


class ChatRequest(BaseModel):
    """Request payload for JanSahayak conversational AI endpoint."""
    message: str = Field(..., description="User query or message in natural language")
    language: Language = Field(default=Language.ENGLISH, description="Preferred language for conversation")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation history for context preservation"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session tracking identifier"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document ID if conversation is scoped to an uploaded PDF"
    )
    include_audio: bool = Field(
        default=False,
        description="Whether to generate and return text-to-speech audio for the answer"
    )


class SourceCitation(BaseModel):
    """Official citation metadata supporting any claim made by JanSahayak."""
    title: str = Field(..., description="Title of the source or document")
    url: Optional[str] = Field(default=None, description="Direct URL to official portal or PDF")
    source_type: str = Field(
        ...,
        description="'official_api', 'official_website', or 'uploaded_document'"
    )
    page_number: Optional[int] = Field(default=None, description="Page number if derived from a document")
    section: Optional[str] = Field(default=None, description="Section heading or clause identifier")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of source retrieval"
    )
    is_verified: bool = Field(default=True, description="Whether source authenticity is verified")


class ChatResponse(BaseModel):
    """Complete response returned by the JanSahayak orchestrator."""
    answer: str = Field(..., description="Simple, clear answer tailored to the citizen")
    language: Language = Field(..., description="Language in which response is formulated")
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Verified government citations backing the answer"
    )
    agent_steps: List[str] = Field(
        default_factory=list,
        description="Human-readable transparent trace of steps the AI took"
    )
    has_audio: bool = Field(default=False, description="Whether TTS audio was generated")
    audio_url: Optional[str] = Field(default=None, description="Relative URL to the audio stream")
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Actionable follow-up questions for the citizen"
    )
    eligibility_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured scheme eligibility analysis if applicable"
    )
    session_id: str = Field(..., description="Conversation session identifier")


class GovernmentScheme(BaseModel):
    """Detailed model representing an Indian government welfare scheme."""
    id: str = Field(..., description="Unique scheme ID or slug")
    name: str = Field(..., description="Scheme title in English")
    name_hindi: Optional[str] = Field(default=None, description="Scheme title in Hindi")
    name_telugu: Optional[str] = Field(default=None, description="Scheme title in Telugu")
    description: str = Field(..., description="Detailed description of the scheme's goals and scope")
    ministry: Optional[str] = Field(default=None, description="Central ministry or department managing the scheme")
    state: Optional[str] = Field(default=None, description="State name for state schemes, None for Central schemes")
    beneficiary_types: List[str] = Field(default_factory=list, description="Target groups (e.g. farmers, students)")
    benefits: List[str] = Field(default_factory=list, description="Key monetary or non-monetary benefits provided")
    eligibility_criteria: List[str] = Field(default_factory=list, description="List of criteria required to qualify")
    required_documents: List[str] = Field(default_factory=list, description="Official documents required to apply")
    application_url: Optional[str] = Field(default=None, description="Online portal URL to apply")
    official_url: str = Field(..., description="Official government scheme information portal URL")
    source: str = Field(..., description="Source system e.g. 'myscheme', 'india_gov', 'data_gov'")
    last_verified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last verified timestamp"
    )
    category: Optional[str] = Field(default=None, description="Scheme sector/category e.g. 'Agriculture', 'Education'")


class SchemeSearchRequest(BaseModel):
    """Parameters for searching government schemes."""
    query: Optional[str] = Field(default=None, description="Search keyword or query")
    state: Optional[str] = Field(default=None, description="Filter by Indian State / UT")
    category: Optional[str] = Field(default=None, description="Filter by category")
    beneficiary_type: Optional[str] = Field(default=None, description="Filter by beneficiary group")
    language: Language = Field(default=Language.ENGLISH, description="Preferred language for output")


class SchemeSearchResponse(BaseModel):
    """Response payload for scheme searches."""
    schemes: List[GovernmentScheme] = Field(default_factory=list, description="Matching government schemes")
    total: int = Field(default=0, description="Total number of matching schemes found")
    source: str = Field(..., description="Official source(s) queried")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of retrieval"
    )
    warning: Optional[str] = Field(default=None, description="Notice if any source was unreachable")


class EligibilityProfile(BaseModel):
    """Citizen demographic and socio-economic profile for scheme matching."""
    age: Optional[int] = Field(default=None, description="Age in years")
    state: Optional[str] = Field(default=None, description="Resident Indian state")
    occupation: Optional[str] = Field(default=None, description="Occupation (e.g., 'farmer', 'student', 'artisan')")
    annual_income: Optional[float] = Field(default=None, description="Annual household income in INR")
    is_student: Optional[bool] = Field(default=None, description="Whether currently enrolled as a student")
    is_employed: Optional[bool] = Field(default=None, description="Current employment status")
    gender: Optional[str] = Field(default=None, description="'female', 'male', 'transgender', 'other'")
    category: Optional[str] = Field(
        default=None,
        description="Social category ('General', 'OBC', 'SC', 'ST') — requested only if legally mandated"
    )
    additional_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra attributes such as land ownership, disability percentage, marital status"
    )


class EligibilityResult(BaseModel):
    """Detailed eligibility assessment for a specific government scheme."""
    scheme: GovernmentScheme = Field(..., description="The evaluated scheme")
    status: str = Field(
        ...,
        description="'likely_eligible', 'possibly_eligible', 'not_eligible', or 'insufficient_info'"
    )
    satisfied_conditions: List[str] = Field(default_factory=list, description="Criteria met by the user")
    unsatisfied_conditions: List[str] = Field(default_factory=list, description="Criteria clearly not met")
    missing_information: List[str] = Field(default_factory=list, description="Information required to decide")
    required_documents: List[str] = Field(default_factory=list, description="Documents user must prepare")
    application_steps: List[str] = Field(default_factory=list, description="Step-by-step instructions to apply")
    official_link: Optional[str] = Field(default=None, description="Direct portal to apply or verify")
    disclaimer: str = Field(
        default=(
            "This eligibility assessment is for guidance only and does not constitute a legal guarantee. "
            "Final verification and sanction rests with the respective government department."
        ),
        description="Official disclaimer"
    )
    sources: List[SourceCitation] = Field(default_factory=list, description="Official sources used for evaluation")


class DocumentUploadResponse(BaseModel):
    """Metadata and initial extraction summary of an uploaded government document."""
    document_id: str = Field(..., description="Unique document UUID")
    filename: str = Field(..., description="Original filename of the uploaded file")
    page_count: int = Field(..., description="Total number of pages processed")
    extracted_text_preview: str = Field(..., description="Preview snippet of extracted text")
    key_clauses: List[str] = Field(default_factory=list, description="Primary clauses or articles detected")
    important_dates: List[str] = Field(default_factory=list, description="Key deadlines, launch dates, or cutoffs")
    eligibility_mentions: List[str] = Field(default_factory=list, description="Eligibility criteria excerpts found")
    required_documents_mentioned: List[str] = Field(
        default_factory=list,
        description="Checklist of documents mentioned in the PDF"
    )
    language_detected: str = Field(default="en", description="Detected language code of the document")
    processing_notes: List[str] = Field(default_factory=list, description="Notices on OCR, fallback, or indexing status")
    is_scanned: bool = Field(default=False, description="Whether document is an image scan without digital text")
    document_type: Optional[str] = Field(default=None, description="Inferred or extracted document classification")


class DocumentQueryRequest(BaseModel):
    """Citizen query directed to an uploaded policy/guideline PDF."""
    document_id: str = Field(..., description="ID of the previously uploaded document")
    question: str = Field(..., description="Citizen's question regarding the document")
    language: Language = Field(default=Language.ENGLISH, description="Preferred language for the answer")


class DocumentQueryResponse(BaseModel):
    """Grounded answer extracted from an uploaded government document."""
    answer: str = Field(..., description="Simplified citizen-friendly answer")
    relevant_passages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Passages with page numbers and confidence scores"
    )
    sources: List[SourceCitation] = Field(default_factory=list, description="Document page citations")
    language: Language = Field(..., description="Language of response")


class VoiceRequest(BaseModel):
    """Request to convert citizen-facing text to synthesized audio."""
    text: str = Field(..., description="Text to synthesize")
    language: Language = Field(default=Language.ENGLISH, description="Spoken language")


class VoiceResponse(BaseModel):
    """Response containing audio file stream link and metadata."""
    audio_url: str = Field(..., description="Endpoint path to stream the generated MP3")
    duration_seconds: Optional[float] = Field(default=None, description="Estimated audio duration in seconds")
    language: Language = Field(..., description="Spoken language")
