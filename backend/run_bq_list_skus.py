from app.data.bigquery_client import list_skus

if __name__ == '__main__':
    skus = list_skus()
    print('count:', len(skus))
    print(skus[:60])
