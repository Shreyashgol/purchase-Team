from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_order":
        raise HTTPException(status_code=400, detail="Sales order create agent received a non-sales-order intent.")
    if not intent.cardCode:
        raise HTTPException(status_code=400, detail="Customer CardCode is required to create a sales order.")
    if not intent.items:
        raise HTTPException(status_code=400, detail="At least one line item is required to create a sales order.")

    result = repository.create_document(intent)
    return SalesActionResponse(
        status="created",
        message=f"Created sales order for customer {intent.cardCode}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_order",
            "agent": "sales_order.create_agent",
            "workflow": ["validate customer and lines", "create sales order", "persist to shared database"],
        },
    )
