from app.operations.sales_rag import build_sales_rag_fetch_sql
from app.operations.sql_executor import execute_read_only_sql
from app.schema.response import SalesActionResponse


def execute(intent, repository) -> SalesActionResponse:
    del repository

    question = intent.fetchQuery or "show sales invoices"
    query_spec = build_sales_rag_fetch_sql(question)
    rows = execute_read_only_sql(query_spec["sql"], query_spec["params"])

    return SalesActionResponse(
        status="success",
        message=f"Sales invoice fetch completed successfully. {len(rows)} result(s) returned.",
        data={
            "sql": query_spec["sql"],
            "filters": query_spec["filters"],
            "results": rows,
            "rowCount": len(rows),
            "strategy": "rag",
            "team": "sales",
            "documentType": "ar_invoice",
            "agent": "sales_invoice.fetch_agent",
        },
    )
