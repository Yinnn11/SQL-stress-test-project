import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": "stressdb",
    "user": "postgres",
    "password": "test1234",
    "host": "localhost",
    "port": "5432",
}

db_pool: Optional[pool.ThreadedConnectionPool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=5, maxconn=20, cursor_factory=RealDictCursor, **DB_CONFIG
    )
    print("✅ PostgreSQL 連線池已成功初始化！")
    yield
    if db_pool:
        db_pool.closeall()
        print("🛑 PostgreSQL 連線池已關閉。")


app = FastAPI(title="Taxi Operations Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    if db_pool is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection pool is not initialized",
        )
    return db_pool.getconn()


def release_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"message": "API 服務正常運作中！"}


@app.get("/trips")
def get_trips(
    limit: int = 10, min_distance: float = 0.0, sort_by: str = "latest"
) -> List[Dict]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            order_clause = "ORDER BY tpep_pickup_datetime DESC"
            if sort_by == "longest":
                order_clause = "ORDER BY trip_distance DESC"

            query = f"""
                SELECT 
                    tpep_pickup_datetime,
                    passenger_count,
                    trip_distance,
                    COALESCE(total_amount::numeric, 0)::float AS total_amount
                FROM taxi_trips 
                WHERE trip_distance >= %s 
                {order_clause} 
                LIMIT %s
            """
            cur.execute(query, (min_distance, limit))
            trips = cur.fetchall()
            return trips
    except Exception as e:
        print(f"❌ Trips Query Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database query error: {str(e)}"
        )
    finally:
        release_db_connection(conn)


@app.get("/stats/analytics")
def get_analytics() -> Dict:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*)::bigint AS total_trips,
                    COALESCE(ROUND(AVG(trip_distance::numeric), 2), 0)::float AS avg_distance
                FROM taxi_trips
            """)
            basic_stats = cur.fetchone()

            cur.execute("""
                SELECT 
                    EXTRACT(HOUR FROM tpep_pickup_datetime::timestamp)::int AS peak_hour,
                    COALESCE(SUM(passenger_count::numeric), 0)::bigint AS total_passengers
                FROM taxi_trips
                WHERE tpep_pickup_datetime IS NOT NULL
                GROUP BY peak_hour
                ORDER BY total_passengers DESC
                LIMIT 1
            """)
            peak_stats = cur.fetchone()

            return {
                "total_trips": (
                    basic_stats["total_trips"]
                    if basic_stats and basic_stats["total_trips"]
                    else 0
                ),
                "avg_distance": (
                    basic_stats["avg_distance"]
                    if basic_stats and basic_stats["avg_distance"]
                    else 0.0
                ),
                "peak_hour": (
                    peak_stats["peak_hour"]
                    if peak_stats and peak_stats["peak_hour"] is not None
                    else 0
                ),
                "peak_passengers": (
                    peak_stats["total_passengers"]
                    if peak_stats and peak_stats["total_passengers"]
                    else 0
                ),
            }
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database query error: {str(e)}"
        )
    finally:
        release_db_connection(conn)