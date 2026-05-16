from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_return":
        raise HTTPException(status_code=400, detail="Sales return create agent received a non-return intent.")
    if not intent.cardCode:
        raise HTTPException(status_code=400, detail="Customer CardCode is required to create a sales return.")
    if not intent.items:
        raise HTTPException(status_code=400, detail="At least one line item is required to create a sales return.")

    result = repository.create_document(intent)
    return SalesActionResponse(
        status="created",
        message=f"Created sales return for customer {intent.cardCode}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_return",
            "agent": "sales_return.create_agent",
            "workflow": ["validate customer and return lines", "create sales return", "persist to shared database"],
        },
    )
