"""
Chat API Router.
Endpoint untuk interaksi real-time guru dengan DyLeks AI Pedagogical Copilot.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ollama_service import copilot_service

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_with_copilot(payload: ChatRequest):
    """
    Endpoint untuk guru bertanya ke DyLeks AI Copilot.
    Copilot bisa menerima context hasil skrining anak untuk rekomendasi yang lebih personal.
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    # Konversi context Pydantic model ke dict jika ada
    context_dict = payload.context.model_dump() if payload.context else None

    ai_reply = await copilot_service.get_reply(
        message=payload.message,
        context=context_dict
    )

    return ChatResponse(reply=ai_reply)