from fastapi import HTTPException

from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    if intent.documentType != "sales_return":
        raise HTTPException(status_code=400, detail="Sales return update agent received a non-return intent.")
    if not intent.docEntry:
        raise HTTPException(status_code=400, detail="DocEntry is required to update a sales return.")

    result = repository.update_document(intent)
    if not result:
        raise HTTPException(status_code=404, detail=f"Sales return {intent.docEntry} was not found.")

    return SalesActionResponse(
        status="updated",
        message=f"Updated sales return {intent.docEntry}.",
        data={
            "postgresRecord": result,
            "team": "sales",
            "documentType": "sales_return",
            "agent": "sales_return.update_agent",
            "workflow": ["load existing return", "apply requested changes", "persist to shared database"],
        },
    )
