from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "ar_invoice":
        raise HTTPException(status_code=400, detail="Sales invoice cancel agent received a non-invoice intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to cancel a sales invoice.")

    result = repository.set_status("ar_invoice", intent.docEntry, "cancelled")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales invoice {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="cancelled",
        message=f"Cancelled sales invoice {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "ar_invoice",
            "agent": "sales_invoice.cancel_agent",
            "workflow": ["load current invoice status", "mark invoice cancelled", "persist to shared database"],
        },
    )
