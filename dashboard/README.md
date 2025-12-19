## Demand Forecasting Dashboard

This is a local-first, production-style dashboard for visualising retail and ecommerce demand forecasts.

It is built with **Next.js (App Router)**, **TypeScript**, **Tailwind CSS**, **Recharts**, and **Axios**, and consumes the FastAPI backend at `http://localhost:8000`.

### Prerequisites

- Node.js 18+
- The backend FastAPI service running locally on port `8000` with a trained model and generated metrics.

### Running the Backend

From the `demand_forecasting/backend` directory:

1. Create and activate a Python 3.10+ environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the offline training pipeline (example invocation, adjust paths as needed):

```bash
python src/ingest.py --input_csv path/to/your_sales.csv
python src/features.py
python src/split.py
python src/train.py         # or src/tune.py for tuned model
python src/evaluate.py
```

4. Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

### Running the Dashboard

From the `demand_forecasting/dashboard` directory:

```bash
npm install
npm run dev
```

Then open `http://localhost:3000` in your browser.

The dashboard will:

- Load available SKUs from `GET http://localhost:8000/skus`
- Load forecast data from `GET http://localhost:8000/forecast/{sku}?horizon=7|14|30`
- Load model metrics (MAE, RMSE) from `GET http://localhost:8000/metrics`


