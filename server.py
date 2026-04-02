#!/usr/bin/env python3
"""FastAPI server for Mining Globe."""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = "mines.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    cesium_token = os.getenv("CESIUM_ION_TOKEN", "")
    html = Path("index.html").read_text()
    return HTMLResponse(content=html.replace("{{CESIUM_ION_TOKEN}}", cesium_token))


@app.get("/api/mines")
def get_mines(
    commodity: str = Query(default=None),
    country: str = Query(default=None),
    status: str = Query(default=None),
    search: str = Query(default=None),
):
    conn = get_db()
    query = "SELECT * FROM mines WHERE lat IS NOT NULL"
    params = []

    if commodity:
        query += " AND commodity LIKE ?"
        params.append(f"%{commodity}%")
    if country:
        query += " AND country = ?"
        params.append(country)
    if status:
        query += " AND status = ?"
        params.append(status)
    if search:
        query += " AND (mine_name LIKE ? OR operator LIKE ? OR owning_company LIKE ? OR ticker LIKE ?)"
        params.extend([f"%{search}%"] * 4)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM mines WHERE lat IS NOT NULL").fetchone()["c"]
    countries = conn.execute("SELECT COUNT(DISTINCT country) as c FROM mines WHERE lat IS NOT NULL").fetchone()["c"]
    commodities = conn.execute("SELECT DISTINCT commodity FROM mines WHERE lat IS NOT NULL AND commodity IS NOT NULL ORDER BY commodity").fetchall()
    country_list = conn.execute("SELECT DISTINCT country FROM mines WHERE lat IS NOT NULL ORDER BY country").fetchall()
    conn.close()
    return {
        "total_mines": total,
        "countries": countries,
        "commodity_list": [r["commodity"] for r in commodities],
        "country_list": [r["country"] for r in country_list],
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Mining Globe at http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
