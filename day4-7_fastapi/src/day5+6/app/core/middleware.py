""" 
Apply middleware 
"""

import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

logger = logging.getLogger("app.middleware")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def parse_allowed_origins() -> list[str]:
    origins_str = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    if origins_str == "*":
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

""" 
Các middleware được thiết lập của project bao gồm : 

    1. CORS (Cross-Origin Resource Sharing) Middleware 
    2. GZip Middleware 
        -> Nén response từ 1024 bytes để giảm dung lượng truyền tải trước khi trả về cho client !
    3. Request context & Logging Middleware 
    4. Security headers Middleware 
"""



def setup_middlewares(app: FastAPI) -> None:
    allow_origins = parse_allowed_origins()
    allow_credentials = allow_origins != ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        process_ms = (time.perf_counter() - start) * 1000
        
        # Mã định danh của request 
        response.headers["X-Request-ID"] = request_id
        # Kiểu dữ liệu trả về từ server mà browser cần tuân theo 
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Hạn chế được clickjacking 
        response.headers["X-Frame-Options"] = "DENY"
        # Kiểm soát thông tin browser gửi về trang trước đó khi user chuyển trang, gửi request 
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            process_ms,
        )
        return response
