from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_order":
        raise HTTPException(status_code=400, detail="Sales order update agent received a non-sales-order intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to update a sales order.")

    result = repository.update_document(intent)
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales order {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="updated",
        message=f"Updated sales order {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_order",
            "agent": "sales_order.update_agent",
            "workflow": ["load existing sales order", "apply requested changes", "persist to shared database"],
        },
    )
