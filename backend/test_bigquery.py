from app.data.bigquery_client import list_skus, fetch_daily_demand

if __name__ == '__main__':
    try:
        skus = list_skus()
        print('SKUs from BigQuery:', skus[:20])
    except Exception as e:
        print('list_skus error:', repr(e))

    try:
        df = fetch_daily_demand()
        print('daily demand rows:', len(df))
        print(df.head().to_dict(orient='records'))
    except Exception as e:
        print('fetch_daily_demand error:', repr(e))
