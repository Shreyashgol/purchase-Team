from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_return":
        raise HTTPException(status_code=400, detail="Sales return close agent received a non-return intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to close a sales return.")

    result = repository.set_status("sales_return", intent.docEntry, "closed")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales return {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="closed",
        message=f"Closed sales return {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_return",
            "agent": "sales_return.close_agent",
            "workflow": ["load current return status", "mark return closed", "persist to shared database"],
        },
    )
