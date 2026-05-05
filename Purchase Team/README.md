# Purchase Team Supervisor Flow


1. User sends a natural-language purchase-team request.
2. `supervisor_agent` routes the request to `fetch_agent`.
3. `fetch_agent` decides which document agent should handle it:
   - `purchase_order_agent`
   - `ap_invoice_agent`
   - `purchase_return_agent`
4. The selected document agent handles its own `create`, `fetch`, `update`, `close`, or `cancel` subagent.

## Run

Start the three document APIs first, then run:

```bash
cd "/Users/shreyashgolhani/Desktop/sap /Purchase Team"
../myvenv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```
