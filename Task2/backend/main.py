from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
import clickhouse_connect
import os

# ---------------------------------------------------------------------
# Настройки окружения / параметры соединения
# ---------------------------------------------------------------------
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "http://keycloak:8080/realms/reports-realm")
KEYCLOAK_PUBLIC_KEY = os.getenv("KEYCLOAK_PUBLIC_KEY", "")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "airflow")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "airflow")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "airflow_results")

# ---------------------------------------------------------------------
# FastAPI приложение
# ---------------------------------------------------------------------
app = FastAPI(title="Reports API (ClickHouse)")

# Разрешаем фронтенду ходить к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------------------------------------------------------------------
# Проверка токена Keycloak
# ---------------------------------------------------------------------
def verify_token(token: str = Depends(oauth2_scheme)):
    # временно, чтобы фронт без JWT мог работать
    return "1fa38bd4-5af7-489d-895e-e347831e518f"

# ---------------------------------------------------------------------
# Подключение к ClickHouse
# ---------------------------------------------------------------------
def get_ch_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )

# ---------------------------------------------------------------------
# Эндпоинт /reports
# ---------------------------------------------------------------------
@app.get("/reports")
def get_user_report(
    user_id: str = Query(..., description="ID пользователя (UUID)"),
    current_user: str = Depends(verify_token),
):
    """
    Возвращает список заказов пользователя из ClickHouse.
    Доступ только к своим данным.
    """
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Access denied: can only view your own report")

    client = get_ch_client()
    query = """
        SELECT id, order_number, total, discount, buyer_id
        FROM sample_table
        WHERE buyer_id = %(buyer_id)s
    """
    result = client.query(query, parameters={"buyer_id": user_id})

    records = [
        {
            "id": r[0],
            "order_number": r[1],
            "total": float(r[2]),
            "discount": float(r[3]),
            "buyer_id": r[4],
        }
        for r in result.result_rows
    ]

    return {"user_id": user_id, "records": records}

# ---------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}