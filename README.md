🧺 SMRT Laundry – AI-Powered Order & Pricing Assistant

A full-stack project that combines React Native + Expo for the mobile app and FastAPI + DuckDB for the backend, providing a chat-based interface to explore customer orders, inventory, and pricing data stored in CSVs.

The project is designed to answer data-grounded questions (revenue, orders, pricing) and FAQ-style queries (like "Can I dry clean my blazer?") — all while avoiding LLM hallucinations.

✨ Features

--> Chat Interface – Users can query their data in natural language:

“Total revenue for CID 1000001”

“Show orders between 2025-08-01 and 2025-08-02”

“Top customers by revenue”

--> Hallucination-Free SQL Execution

LLM is never allowed to run raw SQL.

Instead, it produces a structured plan → safe SQL is rendered → validated → executed.

--> Interactive Pricing Page

Pulls data from Pricelist.csv with search and pagination.

Shows icons for common garment types.

--> Customer Reports

Summaries + timeseries revenue per customer.

--> FAQ Support

“How do I schedule a pickup?”

“Can I dry clean wool coats?”

--> Responsive UI

Sky-blue theme with a clean, minimal chat layout.

Works on Web (expo start -w), iOS Simulator, or Android Emulator.

--> Docker Support

API and app can run together in containers for consistent deployment.

🛠 Tech Stack
Layer	Tech
Frontend	React Native + Expo, react-native-paper, victory-native (charts)
Backend	FastAPI, DuckDB, Pandas
AI	Google Gemini (for natural language → SQL planning + FAQs)
Infra	Docker, docker-compose
🚫 How Hallucinations Are Prevented

A key design goal was safe, grounded answers:

Rule-based Intents First – For common patterns like totals, orders, top customers, etc.

LLM Plan, Not SQL – Gemini generates a JSON query plan, not SQL.

SQL Validator – Rejects any unsafe SQL:

Must be a single SELECT

Tables must be in {Customer, Inventory, Detail, Pricelist}

Functions must be in a strict allowlist

Optional Repair Step – If a query fails, Gemini can propose a corrected plan (still validated).

FAQ Mode – For non-data questions, Gemini is used only for text generation, not data access.



🚀 Setup & Run Locally
1) Clone the repo
git clone https://github.com/<your-username>/SMRT_Laundry.git
cd SMRT_Laundry

2) Backend (FastAPI)
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy example env and set your Google API key
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY=your_key_here

# Run API
uvicorn app:app --reload --host 0.0.0.0 --port 8000


Test:
➡ Go to http://localhost:8000/docs
 to try /health or /pricelist.

3) Frontend (React Native / Expo)
cd ../app
npm install
npx expo start -c


Press w to run in the browser (web mode)

Or press i for iOS simulator, a for Android emulator.

4) (Optional) Run with Docker
docker-compose up --build


This spins up both the API (localhost:8000) and Expo bundler.
