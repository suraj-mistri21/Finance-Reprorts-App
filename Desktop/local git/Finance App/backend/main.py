from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import traceback

from payment_report import generate_payment_report
from export_ar_orders import generate_ar_report
from order_report import generate_order_report
from refund_report import generate_refund_report
from partner_master_report import generate_partner_master_report
from partner_location_master_report import generate_partner_location_master_report
import product_master_report


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Finance Reports API",
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Current frontend on VM
        "http://10.219.1.200:3000",

        # Local development
        "http://localhost:3000",
        "http://127.0.0.1:3000",

        "http://localhost:5173",
        "http://127.0.0.1:5173",

        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def home():
    return {
        "status": "Running",
        "application": "Finance Reports API"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Finance Reports API",
        "version": "1.0.0"
    }


# ============================================================
# REQUEST MODEL
# ============================================================

class ReportRequest(BaseModel):
    startDate: str | None = None
    endDate: str | None = None


# ============================================================
# PAYMENT REPORT
# ============================================================

@app.post("/api/payment-report")
def payment_report(request: ReportRequest):
    try:
        filename = generate_payment_report(
            start_date=request.startDate,
            end_date=request.endDate
        )

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/payment-download")
def payment_download():

    filename = "payment_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Payment Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# AR REPORT
# ============================================================

@app.post("/api/ar-report")
def ar_report(request: ReportRequest):
    try:
        filename = generate_ar_report(
            end_date=request.endDate
        )

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/ar-download")
def ar_download():

    filename = "ar_aging_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the AR Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# ORDER REPORT
# ============================================================

@app.post("/api/order-report")
def order_report(request: ReportRequest):
    try:
        filename = generate_order_report(
            start_date=request.startDate,
            end_date=request.endDate
        )

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/order-download")
def order_download():

    filename = "orders_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Order Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# REFUND REPORT
# ============================================================

@app.post("/api/refund-report")
def refund_report(request: ReportRequest):
    try:
        filename = generate_refund_report(
            start_date=request.startDate,
            end_date=request.endDate
        )

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/refund-download")
def refund_download():

    filename = "refund_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Refund Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# PARTNER MASTER
# ============================================================

@app.post("/api/partner-master")
def partner_master():
    try:
        filename = generate_partner_master_report()

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/partner-master-download")
def partner_master_download():

    filename = "partner_master_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Partner Master Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# PRODUCT MASTER
# ============================================================

@app.post("/api/product-master")
def product_master():
    try:
        filename = product_master_report.generate_product_master_report()

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/product-master-download")
def product_master_download():

    filename = "product_master_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Product Master Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )


# ============================================================
# PARTNER LOCATION MASTER
# ============================================================

@app.post("/api/partner-location-master")
def partner_location_master():
    try:
        filename = generate_partner_location_master_report()

        return {
            "status": "success",
            "file": filename
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/partner-location-master-download")
def partner_location_master_download():

    filename = "partner_location_master_report.csv"

    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Generate the Partner Location Master Report first."
        )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="text/csv"
    )