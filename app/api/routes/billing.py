from fastapi import APIRouter, HTTPException

from app.services.paystack_service import list_banks, PaystackError

router = APIRouter()


@router.get("/billing/banks")
async def get_banks():
    """Public — returns SA bank list from Paystack (name + code)."""
    try:
        banks = list_banks()
    except PaystackError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})
    return [{"name": b["name"], "code": b["code"]} for b in banks]
