from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "ar_invoice":
        raise HTTPException(status_code=400, detail="Sales invoice create agent received a non-invoice intent.")
    if not intent.cardCode:
        raise HTTPException(status_code=400, detail="Customer CardCode is required to create a sales invoice.")
    if not intent.items:
        raise HTTPException(status_code=400, detail="At least one line item is required to create a sales invoice.")

    result = repository.create_document(intent)
    return SalesActionResponse(
        status="created",
        message=f"Created sales invoice for customer {intent.cardCode}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "ar_invoice",
            "agent": "sales_invoice.create_agent",
            "workflow": ["validate customer and invoice lines", "create sales invoice", "persist to shared database"],
        },
    )
