from fastapi import FastAPI, HTTPException, status, Request, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database_model import CardioHealthCreate, CardioHealthUpdate, CardioHealthResponse
from db_operations import CardioHealthOperations
from connection_db import init_db, get_session, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

def setup_jinja_filters(templates):
    def days_to_years(days):
        return int(days / 365)
    
    def cm_to_meters(cm):
        return round(cm / 100, 2)
    
    templates.env.filters["days_to_years"] = days_to_years
    templates.env.filters["cm_to_meters"] = cm_to_meters

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Archivos estáticos (CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates HTML
templates = Jinja2Templates(directory="templates")

setup_jinja_filters(templates)

# Ruta de inicio
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/records")
async def display_table(
    request: Request,
    page: int = 1,
    session: AsyncSession = Depends(get_async_session)
):
    result = await CardioHealthOperations.get_all_records(session, page=page)
    return templates.TemplateResponse("table_view.html", {
        "request": request,
        "records": result["data"],
        "page": result["page"],
        "per_page": result["per_page"],
        "total": result["total"]
    })

from fastapi import Form

@app.post("/records/", status_code=status.HTTP_201_CREATED)
async def create_record(
    request: Request,
    age: int = Form(...),
    gender: int = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    ap_hi: int = Form(...),
    ap_lo: int = Form(...),
    cholesterol: int = Form(...),
    gluc: int = Form(...),
    smoke: int = Form(default=0),
    alco: int = Form(default=0),
    active: int = Form(default=0),
    cardio: int = Form(default=0),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        record_data = {
            "age": age * 365,
            "gender": gender,
            "height": height * 100,
            "weight": weight,
            "ap_hi": ap_hi,
            "ap_lo": ap_lo,
            "cholesterol": cholesterol,
            "gluc": gluc,
            "smoke": smoke,
            "alco": alco,
            "active": active,
            "cardio": cardio
        }
        new_record = await CardioHealthOperations.add_record(session, record_data)
        # Redirigir a la página de éxito con el ID del nuevo registro
        return RedirectResponse(
            url=f"/success?id={new_record.id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        await session.rollback()
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": str(e)
            },
            status_code=400
        )

@app.get("/records/{record_id}", response_class=HTMLResponse)
async def read_record(request: Request, record_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        record = await CardioHealthOperations.get_record_by_id(session, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return templates.TemplateResponse("record_detail.html", {
            "request": request,
            "record": record
        })
    except HTTPException as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": e.detail
        }, status_code=e.status_code)

@app.put("/records/{record_id}", response_model=CardioHealthResponse)
async def update_record(record_id: int, record: CardioHealthUpdate):
    async with get_session() as session:
        try:
            updated = await CardioHealthOperations.edit_record(
                session, record_id, record.dict(exclude_unset=True))
            if not updated:
                raise HTTPException(status_code=404, detail="Registro no encontrado")
            return updated
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/records/{record_id}/recommendations", response_class=HTMLResponse)
async def get_recommendations(request: Request, record_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        record = await CardioHealthOperations.get_record_by_id(session, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
            
        recommendations_response = await CardioHealthOperations.get_recommendations(session, record_id)
        if not recommendations_response.get("success"):
            raise HTTPException(status_code=404, detail=recommendations_response.get("message", "Error al obtener recomendaciones"))
            
        return templates.TemplateResponse("recommendations.html", {
            "request": request,
            "record_id": record_id,
            "record": record,
            "recommendations": recommendations_response["data"],
            "message": recommendations_response["message"]
        })
    except HTTPException as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": e.detail
        }, status_code=e.status_code)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "path": request.url.path
        }
    )
@app.get("/success", response_class=HTMLResponse)
async def success_page(
    request: Request,
    id: int,
    session: AsyncSession = Depends(get_async_session)
):
    record = await CardioHealthOperations.get_record_by_id(session, id)
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "record": record
        }
    )