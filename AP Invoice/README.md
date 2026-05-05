# SAP B1 AP Invoice Agent

Separate FastAPI + Streamlit agent for SAP Business One AP invoices.

## Features

- Create AP invoices from natural-language prompts
- Fetch AP invoices with a Text-to-SQL flow over locally persisted invoice data
- JWT-protected API matching the Purchase Order app pattern
- SAP Service Layer integration through `/PurchaseInvoices`
- Local mock SAP server for testing the SAP endpoint flow
- Shared PostgreSQL runtime pattern for reuse across all agents

## Project Structure

```text
AP Invoice/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   │   ├── create_agent.py
│   │   └── fetch_agent.py
│   ├── api/
│   │   ├── auth.py
│   │   └── ap_invoices.py
│   ├── crud/
│   │   └── ap_invoice_crud.py
│   ├── db/
│   │   ├── base.py
│   │   └── models.py
│   ├── model/
│   │   └── ap_invoice_intent.py
│   ├── operations/
│   │   ├── error_handler.py
│   │   ├── intent_parser.py
│   │   ├── sap_client.py
│   │   ├── sql_executor.py
│   │   ├── text_to_sql.py
│   │   └── utils.py
│   └── schema/
│       ├── ap_invoice.py
│       ├── auth.py
│       └── response.py
├── requirements.txt
├── mock_sap_server.py
└── streamlit_app.py
```

## Run

```bash
cd "/Users/shreyashgolhani/Desktop/sap /AP Invoice"
pip install -r requirements.txt
export SAP_AGENTS_DATABASE_URL="postgresql://postgres:password@localhost:5432/sap_agents_db"
python mock_sap_server.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
python -m streamlit run streamlit_app.py
```

## API Endpoints

- `POST /login`
- `POST /ap-invoices/parse-and-execute`

## Create Payload Schema

The AP Invoice create flow supports the original create fields and now persists a broader AP invoice header and line shape locally.

Header fields include identifiers, vendor details, dates, financial summary, payment details, status flags, document links, tax fields, and control metadata such as:

- `DocEntry`, `DocNum`, `Series`, `NumAtCard`
- `CardCode`, `CardName`, `LicTradNum`, `CntctCode`
- `DocDate`, `TaxDate`, `DocDueDate`, `CreateDate`, `UpdateDate`
- `DocCur`, `DocRate`, `DocTotal`, `VatSum`, `DiscSum`, `RoundDif`, `PaidToDate`, `PaidSum`, `BalanceDue`
- `PeyMethod`, `PayBlock`, `CtlAccount`
- `DocStatus`, `CANCELED`, `Confirmed`, `WddStatus`
- `BaseEntry`, `BaseType`, `ReceiptNum`, `TransId`
- `VatPercent`, `VatPaid`, `WTDetails`, `GSTTranTyp`, `TaxInvNo`
- `ShipToCode`, `Project`, `SlpCode`, `Comments`, `OwnerCode`, `Attachment`

Line fields now cover quantity, pricing, tax, 3-way match, inventory, finance, logistics, and control details such as:

- `DocEntry`, `LineNum`, `ItemCode`, `Dscription`
- `Quantity`, `BaseQty`, `OpenQty`, `OpenInvQty`
- `Price`, `PriceBefDi`, `DiscPrcnt`, `LineTotal`, `Currency`, `Rate`, `StockPrice`, `GrossBuyPr`, `GTotal`
- `VatPrcnt`, `VatSum`, `TaxCode`, `TaxType`, `LineVat`
- `BaseType`, `BaseEntry`, `BaseLine`, `PoTrgEntry`, `TrgetEntry`
- `WhsCode`, `InvntSttus`, `StockValue`
- `AcctCode`, `OcrCode`, `Project`
- `ShipToCode`, `ShipToDesc`, `TrnsCode`
- `LineStatus`, `FreeTxt`, `OwnerCode`

## Example Prompts

- `Create an AP invoice for vendor V001 with 2 units of ITEM123 at 150 each with tax code T1`
- `Fetch AP invoice 5001`
- `Show me the latest 5 AP invoices for vendor V001`
- `Show open AP invoices containing ITEM123`

## Fetch Flow

For fetch requests, the AP Invoice agent now follows the same style as the Purchase Order fetch agent:

1. Parse the user prompt into a fetch intent
2. Convert the fetch text into a safe read-only SQL query
3. Execute the SQL against the local AP invoice tables
4. Return the matching rows from the API response

Create requests still go to the SAP Service Layer endpoint first, and successful responses are stored locally so the fetch agent can query them later.
