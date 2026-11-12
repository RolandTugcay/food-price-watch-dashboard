# Philippines Food Price Watch Dashboard

A Flask web dashboard for exploring food-price observations across the Philippines. It presents summary indicators, trends, market and commodity breakdowns, and an interactive province map using data stored in PostgreSQL.

## Table of Contents

- [About the Project](#about-the-project)
- [Data Pipleline](#data-pipeline)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Run Locally](#run-locally)
- [Application Pages and Endpoints](#application-pages-and-endpoints)
- [Database Expectations](#database-expectations)
- [Data and Map Assets](#data-and-map-assets)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

## About the Project

The dashboard helps users explore food prices by commodity, market, region, province, date, unit, and price type.

The data comes from [The World Food Programme (WFP), Philippines - Food Prices](https://data.humdata.org/dataset/wfp-food-prices-for-philippines/resource/9a842d72-0d7d-4922-ad0e-eb8106c1ab0e), which is refreshed monthly.

The application reads data from a PostgreSQL database hosted on Supabase and renders server-generated pages with interactive charts and maps in the browser.

## Data Pipeline

The data is supplied by the [Food Price Watch Pipeline](https://github.com/RolandTugcay/food-price-watch-pipeline), which performs a weekly ETL (Extract, Transform, Load) from the Philippines - Food Prices .CSV file into a normalized tables in Supabase database.

## Features

- Dashboard summary metrics and filterable price trends.
- Price-observation table with search, sorting, pagination, and selected-observation trends.
- Commodity table and category-level charts.
- Market table and a province map showing price-observation and monitored-commodity counts on hover.

## Technology Stack

### Backend

- Python
- Flask and Jinja
- Flask-SQLAlchemy and SQLAlchemy
- Psycopg 3 PostgreSQL driver
- PostgreSQL (configured for an SSL connection)

### Frontend

- HTML, CSS and Javascript
- Bootstrap 5 and Bootstrap Icons
- [Chart.js](https://www.chartjs.org/) for interactive charts
- [Leaflet](https://leafletjs.com/) for interactive maps

Bootstrap, Bootstrap Icons, Chart.js, Leaflet, and map tiles are loaded from external CDNs/services and require network access in the browser.

## Project Structure

```text
FoodPriceWatchDashboard/
├── app.py                       # Flask routes and page data preparation
├── requirements.txt             # Python dependencies
├── src/
│   ├── connection.py            # Database configuration and SQLAlchemy setup
│   ├── helpers.py               # Database and chart-data helpers
│   └── sql_txt.py               # SQL statements used by dashboard pages
├── static/
│   ├── css/styles.css           # Shared styles
│   ├── images/commodity-icons/  # Commodity icons
│   ├── js/                      # Page interactions, charts, and maps
│   └── json/regions/            # Province GeoJSON collections
└── templates/                   # Jinja page templates
```

## Requirements

- Python installed on the development machine.
- Access to a PostgreSQL database containing the expected dashboard data.
- Browser network access for the external frontend libraries and OpenStreetMap tiles.

## Setup

The following commands use PowerShell from the dashboard directory:

```powershell
cd FoodPriceWatchDashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents environment activation, either adjust the execution policy for your user according to your organization's guidance or run the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project directory. Start from `.env.example` and set values for your PostgreSQL instance:

```dotenv
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=postgres
DB_USER=your-database-user
DB_PASSWORD=your-database-password
```

`DB_HOST`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` are required. `DB_PORT` defaults to `5432` when omitted. The connection is configured with `sslmode=require`.

Keep `.env` private; do not commit real credentials.

## Run Locally

With the virtual environment activated:

```powershell
python app.py
```

Or invoke the environment directly:

```powershell
.\.venv\Scripts\python.exe app.py
```

The application uses Flask's development server when run this way. Visit `http://127.0.0.1:5000/` in a browser. Do not use the development server or Flask debug mode as a production deployment configuration.

## Application Pages and Endpoints

| Path | Purpose |
| --- | --- |
| `/` | Overview dashboard with filters, summary metrics, charts, and a province map |
| `/price-observations` | Searchable and sortable price-observation table with price trends |
| `/commodities` | Commodity listing and category breakdown charts |
| `/markets` | Market listing and province record-distribution map |
| `/about` | Project information page |
| `/health/db` | Checks whether the configured database connection is available |

The dashboard pages use query parameters for filtering, search, sorting, and pagination.

## Database Expectations

The SQL in `src/sql_txt.py` expects the database to provide:

- Tables: `price_observations`, `markets`, `commodities`, and `categories`.
- View: `v_price_observations`, used by overview trend and price queries.
- Relationships between observations, commodities, categories, and markets through their respective IDs.

The application repository does not create or migrate these database objects. Prepare the database separately before starting the dashboard. The health endpoint checks connectivity only; it does not verify that all required tables, views, or columns exist.

## Data and Map Assets

Province boundaries are stored as GeoJSON files under `static/json/regions/` and are loaded by the browser for the overview and markets maps. The market map groups observation and commodity counts by province and matches database province names against GeoJSON feature names, with aliases for selected renamed provinces.

## Troubleshooting

- **Application reports missing database environment variables:** Check that `.env` is in the dashboard project directory and contains the required `DB_*` values.
- **Database connection fails:** Verify the host, port, user, password, network access, and PostgreSQL SSL configuration. Check `/health/db` for a connection status.
- **A page fails while loading data:** Confirm the database schema and view expected by the SQL in `src/sql_txt.py` are available to the configured user.
- **Charts or maps are blank:** Check the browser console and network panel. Confirm the page's JSON data rendered, the relevant JavaScript loaded, local GeoJSON requests succeeded, and CDN resources are reachable.
- **Map tiles do not appear:** Confirm the browser can access OpenStreetMap tile services; the province boundaries are separate local assets.

## Security Notes

- Never commit `.env` or other credentials.
- Use a production WSGI server and disable Flask debug mode when deploying.
- Restrict database credentials to the permissions required by the dashboard.
- Keep external frontend dependencies and data-source terms in mind when deploying or redistributing the application.
