from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_return":
        raise HTTPException(status_code=400, detail="Sales return cancel agent received a non-return intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to cancel a sales return.")

    result = repository.set_status("sales_return", intent.docEntry, "cancelled")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales return {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="cancelled",
        message=f"Cancelled sales return {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_return",
            "agent": "sales_return.cancel_agent",
            "workflow": ["load current return status", "mark return cancelled", "persist to shared database"],
        },
    )
