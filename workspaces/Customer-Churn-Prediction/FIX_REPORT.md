# ChurnShield Pro - Corrected Build Notes

## Fixed

1. **Scrolling layout**
   - App shell is now `h-screen overflow-hidden`.
   - Left sidebar is fixed/sticky and no longer scrolls with the page.
   - Only the right page content area scrolls.

2. **Frontend speed**
   - Existing lazy loading is preserved.
   - Main layout no longer triggers full body scroll repaint.
   - Upload timeout increased to 10 minutes for large datasets.
   - File upload size increased to 1GB in frontend.

3. **Backend upload speed**
   - CSV uploads are processed in chunks instead of loading the whole file at once.
   - Validation reads only a small sample/header instead of the full dataset.
   - MongoDB writes use unordered bulk upserts in batches.
   - XGBoost/model loading is cached to avoid reloading the model for every customer.
   - Large source column storage is disabled by default for speed.

4. **Backend runtime speed**
   - MongoDB connection pool size increased.
   - Connection timeout tuned for faster failure when Atlas is unreachable.
   - Customer cache and query limit settings remain available for dashboard speed.

## Important performance environment variables

Add/change these in `backend/.env` or Vercel backend environment variables:

```env
MAX_UPLOAD_MB=1024
CSV_CHUNK_SIZE=25000
UPLOAD_BATCH_SIZE=5000
SAVE_SOURCE_COLUMNS=false
CUSTOMER_CACHE_TTL_SECONDS=15
CUSTOMER_QUERY_LIMIT=5000
```

## Run

Backend:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Production frontend build was tested successfully with `npm run build`.
