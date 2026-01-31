from typing import Any, Dict, Optional
from fastapi import HTTPException, status


# -------------------------------------------------------------------
# SUCCESS RESPONSE
# -------------------------------------------------------------------

def success(
    message: str,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    response = {
        "status": "success",
        "message": message,
    }

    if data is not None:
        response["data"] = data

    return response


# -------------------------------------------------------------------
# ERROR RESPONSE
# -------------------------------------------------------------------

def error(
    message: str,
    code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
) -> None:

    payload = {
        "status": "error",
        "message": message,
    }

    if error_code:
        payload["error_code"] = error_code

    raise HTTPException(
        status_code=code,
        detail=payload,
    )
