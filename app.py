from fastapi import FastAPI, HTTPException, Body, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

app = FastAPI()

deliveries = {}
next_id = 1

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse({"error": "Validation error"}, status_code=400)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
def create_delivery(data: dict = Body(...)):
    global next_id
    
    if "recipient" not in data or "address" not in data:
        raise HTTPException(status_code=400, detail="Missing fields")
    
    if not isinstance(data["recipient"], str) or not isinstance(data["address"], str):
        raise HTTPException(status_code=400, detail="Fields must be strings")
        
    if not data["recipient"].strip() or not data["address"].strip():
        raise HTTPException(status_code=400, detail="Fields cannot be empty")

    new_delivery = {
        "id": next_id,
        "recipient": data["recipient"],
        "address": data["address"],
        "status": "created"
    }
    
    deliveries[next_id] = new_delivery
    next_id += 1
    
    return new_delivery


@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return deliveries[delivery_id]


@app.patch("/deliveries/{delivery_id}/status")
def update_status(delivery_id: int, data: dict = Body(...)):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")
        
    if "status" not in data:
        raise HTTPException(status_code=400, detail="Missing status field")
        
    new_status = data["status"]
    valid_statuses = ["created", "in_transit", "delivered"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")
        
    current_status = deliveries[delivery_id]["status"]
    
    valid_transitions = {
        "created": "in_transit",
        "in_transit": "delivered",
        "delivered": None
    }
    
    if valid_transitions.get(current_status) != new_status:
        raise HTTPException(status_code=409, detail="Invalid state transition")
        
    deliveries[delivery_id]["status"] = new_status
    return deliveries[delivery_id]


# --- הקוד החדש עבור תיקיות 5 ו-6 ---

@app.get("/deliveries")
def list_deliveries(status: Optional[str] = None):
    if status:
        valid_statuses = ["created", "in_transit", "delivered"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        
        # סינון הרשימה לפי הסטטוס שביקשו
        filtered_deliveries = [d for d in deliveries.values() if d["status"] == status]
        return filtered_deliveries
        
    # אם אין סינון, מחזירים את כל המילון כרשימה
    return list(deliveries.values())


@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")
        
    # מותר למחוק רק משלוח שעדיין בסטטוס "created"
    if deliveries[delivery_id]["status"] != "created":
        raise HTTPException(status_code=409, detail="Cannot delete a delivery that is in transit or delivered")
        
    del deliveries[delivery_id]
    
    # החזרת סטטוס 204 בלי תוכן, בדיוק לפי ההנחיות
    return Response(status_code=204)