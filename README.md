# Waste Management System


## Persistent Database / Render Deployment

This version supports **PostgreSQL for production** and keeps SQLite as a local-development fallback.

### Render setup
1. Create a PostgreSQL database in Render.
2. Copy its **Internal Database URL**.
3. In the Waste Management web service, open **Environment Variables**.
4. Add:
   - `DATABASE_URL` = Render PostgreSQL Internal Database URL
   - `SECRET_KEY` = a long random secret value
5. Keep the start command:
   `gunicorn app:app`
6. Deploy/redeploy.

When `DATABASE_URL` is present, all users, waste reports, notifications and status updates are stored in PostgreSQL, so they remain available after a new day, restart or redeploy.

**Note:** uploaded images are still stored under `static/uploads`. Render's local filesystem is not persistent for uploaded files; use object storage later if permanent image retention is required.
