from fastapi import APIRouter, HTTPException, Depends
from src.api.models.code_assistant import CodeRequest, CodeResponse
from src.services.code_assistant import CodeAssistantService
from src.core.exceptions import CodeAssistantError

router = APIRouter()

@router.post("/assist", response_model=CodeResponse, name="code_assistant:assist")
async def get_code_assistance(
    request: CodeRequest,
    service: CodeAssistantService = Depends()
) -> CodeResponse:
    """Get code assistance"""
    try:
        return await service.process_request(request)
    except CodeAssistantError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 