# Flask backend

This backend serves the built Angular app and exposes a small API under `/api`.

## Setup

1. Build the Angular frontend:
   - `cd /home/sonat/szkolenia/AiBielikApka/app`
   - `npm install`
   - `npm run build`

2. Create a Python environment and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r /home/sonat/szkolenia/AiBielikApka/app/src/backend/requirements.txt`

3. Run the server:
   - `python /home/sonat/szkolenia/AiBielikApka/app/src/backend/app.py`

The app will be available at `http://localhost:5000/`.

## Notes

- For development with `ng serve` on port 4200, CORS is enabled for `/api/*`.
- The server expects the Angular build output in `app/dist/app`.
