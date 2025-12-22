BigQuery Access (ADC) and Service Account

The backend uses Google BigQuery via Application Default Credentials (ADC). You can provide credentials in two ways:

1) Use gcloud ADC (recommended for dev):
   - Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
   - Authenticate with your user credentials:
     ```powershell
     gcloud auth application-default login
     ```
   - This will store ADC in your local environment for the `google-cloud-bigquery` library to pick up.

2) Use a Service Account JSON (recommended for CI or production):
   - Create a service account in the Google Cloud Console with BigQuery read permissions.
   - Download the JSON key file and store it securely.
   - Set the environment variable before running the backend:
     ```powershell
     $env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\path\to\service-account.json'
     python -m uvicorn app.main:app --reload
     ```

Which tables/columns the backend expects (see `app/data/bigquery_client.py`):
- `orders` table: order_id, user_id, order_date (TIMESTAMP), status, revenue, product_ids (comma-separated)
- `products` table: category, brand, name, image_url, description, tags, sku_id, super_category, price
- `events` table: event_date, event_timestamp, items_item_id, items_quantity, items_price, ...
- `users` table: user_id, created_at, ...

Returned DataFrame columns from `fetch_demand_with_context()`:
- `date`, `sku`, `total_quantity`, `event_count`, `active_users`, `product_category`, `price`

If you want me to run a live query, either run `gcloud auth application-default login` in this environment, or upload a service account JSON and tell me its path so I can set `GOOGLE_APPLICATION_CREDENTIALS` before querying.
