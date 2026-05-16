from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "ar_invoice":
        raise HTTPException(status_code=400, detail="Sales invoice close agent received a non-invoice intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to close a sales invoice.")

    result = repository.set_status("ar_invoice", intent.docEntry, "closed")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales invoice {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="closed",
        message=f"Closed sales invoice {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "ar_invoice",
            "agent": "sales_invoice.close_agent",
            "workflow": ["load current invoice status", "mark invoice closed", "persist to shared database"],
        },
    )
