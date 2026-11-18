# Groundwater Guardian frontend

React + Vite JavaScript starter for the Groundwater Guardian FastAPI backend.

## Run on Windows PowerShell

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

## Backend

Start the FastAPI backend separately. The default API URL is `http://127.0.0.1:8000`.
Change `VITE_API_BASE_URL` in `.env.local` if needed, then restart Vite.

Backend API documentation: http://127.0.0.1:8000/docs

## Important integration notes

- This frontend uses only routes listed in the supplied handoff.
- The backend's exact response schemas and POST/PATCH request bodies must be confirmed in Swagger.
- `unwrapList` supports common list wrappers; adjust it if the actual API uses another response envelope.
- The maintenance create/update payloads are provisional until verified against the live OpenAPI schema.
- If browser requests fail with CORS errors, ask the backend developer to allow `http://localhost:5173` and `http://127.0.0.1:5173`. Do not disable browser security.
- Empty data is displayed as empty; no production records are fabricated.
- The station directory currently displays fields documented in the handoff. Add station detail/reliability drill-down after verifying those response schemas.
