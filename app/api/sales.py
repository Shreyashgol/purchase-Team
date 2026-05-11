from fastapi import APIRouter, Depends, HTTPException

from app.operations.sales_rag import generate_sales_sql
from app.operations.sql_executor import execute_read_only_sql
from app.operations.utils import verify_jwt_token
from app.schema.purchase_order import PromptRequest
from app.schema.response import SalesActionResponse

router = APIRouter()


@router.post("/parse-and-execute", response_model=SalesActionResponse)
def sales_parse_and_execute(request: PromptRequest, user: str = Depends(verify_jwt_token)):
    del user

    try:
        sql = generate_sales_sql(request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sales SQL generation failed: {str(exc)}") from exc

    try:
        results = execute_read_only_sql(sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Sales query execution failed: {str(exc)}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"HANA execution error: {str(exc)}") from exc

    return SalesActionResponse(
        status="success",
        message=f"Sales query executed successfully. {len(results)} result(s) returned.",
        data={
            "sql": sql,
            "results": results,
            "rowCount": len(results),
            "strategy": "rag",
            "team": "sales",
        },
    )
