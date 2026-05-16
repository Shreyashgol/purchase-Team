from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "ar_invoice":
        raise HTTPException(status_code=400, detail="Sales invoice update agent received a non-invoice intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to update a sales invoice.")

    result = repository.update_document(intent)
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales invoice {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="updated",
        message=f"Updated sales invoice {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "ar_invoice",
            "agent": "sales_invoice.update_agent",
            "workflow": ["load existing invoice", "apply requested changes", "persist to shared database"],
        },
    )
