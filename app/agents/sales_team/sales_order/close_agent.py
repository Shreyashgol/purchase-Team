from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_order":
        raise HTTPException(status_code=400, detail="Sales order close agent received a non-sales-order intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to close a sales order.")

    result = repository.set_status("sales_order", intent.docEntry, "closed")
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales order {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="closed",
        message=f"Closed sales order {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_order",
            "agent": "sales_order.close_agent",
            "workflow": ["load current sales order status", "mark order closed", "persist to shared database"],
        },
    )
