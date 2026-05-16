from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_order":
        raise HTTPException(status_code=400, detail="Sales order cancel agent received a non-sales-order intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to cancel a sales order.")

    result = repository.set_status("sales_order", intent.docEntry, "cancelled")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales order {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="cancelled",
        message=f"Cancelled sales order {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_order",
            "agent": "sales_order.cancel_agent",
            "workflow": ["load current sales order status", "mark order cancelled", "persist to shared database"],
        },
    )
