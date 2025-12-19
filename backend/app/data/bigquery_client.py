from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "ai-practice-479405"
DATASET_ID = "sample_data_for_ml_models"

ORDERS_TABLE = f"`{PROJECT_ID}.{DATASET_ID}.orders`"
PRODUCTS_TABLE = f"`{PROJECT_ID}.{DATASET_ID}.products`"
EVENTS_TABLE = f"`{PROJECT_ID}.{DATASET_ID}.events`"
USERS_TABLE = f"`{PROJECT_ID}.{DATASET_ID}.users`"


def get_bq_client() -> bigquery.Client:
    """
    Return a BigQuery client using Application Default Credentials.

    Authentication is handled externally via:
      gcloud auth application-default login
    """
    return bigquery.Client(project=PROJECT_ID)


def fetch_daily_demand(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sku: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch daily demand time series from orders only.

    The `orders` table schema (provided):
      - order_id STRING
      - user_id STRING
      - order_date TIMESTAMP
      - status STRING
      - revenue FLOAT
      - product_ids STRING (comma-separated product identifiers)

    We explode `product_ids` and treat each product occurrence as quantity 1.

    Returns a DataFrame with columns:
      - date (datetime64)
      - sku  (string, derived from product_ids)
      - total_quantity (float)
    """
    client = get_bq_client()

    query = f"""
    WITH exploded_orders AS (
      SELECT
        order_id,
        user_id,
        order_date,
        status,
        revenue,
        TRIM(pid) AS sku
      FROM {ORDERS_TABLE},
      UNNEST(SPLIT(product_ids, ',')) AS pid
    )
    SELECT
      DATE(order_date) AS date,
      sku,
      COUNT(*) AS total_quantity
    FROM exploded_orders
    WHERE 1 = 1
      AND (@start_date IS NULL OR DATE(order_date) >= @start_date)
      AND (@end_date IS NULL OR DATE(order_date) <= @end_date)
      AND (@sku IS NULL OR sku = @sku)
    GROUP BY date, sku
    ORDER BY date, sku
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("sku", "STRING", sku),
        ]
    )

    job = client.query(query, job_config=job_config)
    df = job.result().to_dataframe()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["sku"] = df["sku"].astype(str)
        df["total_quantity"] = df["total_quantity"].astype(float)
    return df


def fetch_demand_with_context(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sku: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch daily demand time series enriched with product, event and user context.

    Schemas (provided):
      orders:
        - order_id STRING
        - user_id STRING
        - order_date TIMESTAMP
        - status STRING
        - revenue FLOAT
        - product_ids STRING (comma-separated)

      products:
        - category STRING
        - brand STRING
        - name STRING
        - image_url STRING
        - description STRING
        - tags STRING
        - sku_id INTEGER
        - super_category STRING
        - price FLOAT

      events:
        - event_date INTEGER (YYYYMMDD)
        - event_timestamp INTEGER (micros since epoch)
        - items_item_id FLOAT   (we treat as SKU id)
        - items_quantity FLOAT
        - items_price FLOAT
        - ... (many other fields)

      users:
        - user_id STRING
        - created_at TIMESTAMP
        - ... (other attributes)
    """
    client = get_bq_client()

    query = f"""
    WITH exploded_orders AS (
      SELECT
        order_id,
        user_id,
        order_date,
        status,
        revenue,
        TRIM(pid) AS sku
      FROM {ORDERS_TABLE},
      UNNEST(SPLIT(product_ids, ',')) AS pid
    ),
    base_orders AS (
      SELECT
        DATE(order_date) AS date,
        sku,
        COUNT(*) AS total_quantity,
        SUM(revenue) AS total_revenue
      FROM exploded_orders
      WHERE 1 = 1
        AND (@start_date IS NULL OR DATE(order_date) >= @start_date)
        AND (@end_date IS NULL OR DATE(order_date) <= @end_date)
        AND (@sku IS NULL OR sku = @sku)
      GROUP BY date, sku
    ),
    daily_events AS (
      SELECT
        -- prefer event_date if populated, otherwise derive from timestamp
        COALESCE(
          DATE(PARSE_DATE('%Y%m%d', CAST(event_date AS STRING))),
          DATE(TIMESTAMP_MICROS(event_timestamp))
        ) AS date,
        CAST(CAST(items_item_id AS INT64) AS STRING) AS sku,
        COUNT(*) AS event_count,
        SUM(IFNULL(items_quantity, 0)) AS event_quantity,
        SUM(IFNULL(items_price, 0) * IFNULL(items_quantity, 0)) AS event_revenue
      FROM {EVENTS_TABLE}
      GROUP BY date, sku
    ),
    daily_users AS (
      SELECT
        DATE(created_at) AS date,
        COUNT(DISTINCT user_id) AS active_users
      FROM {USERS_TABLE}
      GROUP BY date
    )
    SELECT
      o.date,
      o.sku,
      o.total_quantity,
      e.event_count,
      u.active_users,
      p.category AS product_category,
      p.price
    FROM base_orders o
    LEFT JOIN daily_events e
      ON o.date = e.date AND o.sku = e.sku
    LEFT JOIN daily_users u
      ON o.date = u.date
    LEFT JOIN {PRODUCTS_TABLE} p
      ON o.sku = CAST(p.sku_id AS STRING)
    ORDER BY o.date, o.sku
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("sku", "STRING", sku),
        ]
    )
    job = client.query(query, job_config=job_config)
    df = job.result().to_dataframe()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["sku"] = df["sku"].astype(str)
        df["total_quantity"] = df["total_quantity"].astype(float)
        if "event_count" in df.columns:
            df["event_count"] = df["event_count"].fillna(0.0).astype(float)
        if "active_users" in df.columns:
            df["active_users"] = df["active_users"].fillna(0.0).astype(float)
        if "price" in df.columns:
            df["price"] = df["price"].astype(float)
        if "product_category" in df.columns:
            df["product_category"] = df["product_category"].astype(str)
    return df


def list_skus() -> list[str]:
    """
    Return the distinct set of SKUs present in the orders table.
    """
    client = get_bq_client()

    query = f"""
    SELECT DISTINCT TRIM(pid) AS sku
    FROM {ORDERS_TABLE},
    UNNEST(SPLIT(product_ids, ',')) AS pid
    WHERE TRIM(pid) IS NOT NULL
    ORDER BY sku
    """

    job = client.query(query)
    df = job.result().to_dataframe()
    if df.empty:
        return []
    return df["sku"].astype(str).tolist()


