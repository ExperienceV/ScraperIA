from icecream import ic
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from functions.aliexpress_scraper import run
from fastapi.middleware.cors import CORSMiddleware
from functions.llm_integration import rank_products_with_llm
from pathlib import Path

app = FastAPI(
    title="AliExpress Scraper API",
    description="API for scraping and ranking AliExpress products using AI",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, reemplaza "*" con tu dominio
    allow_methods=["*"],
    allow_headers=["*"],
)

# Experience Endpoints

@app.get("/", response_class=HTMLResponse)
async def welcome():
    """
    Root endpoint that returns a welcome page with API documentation.
    
    Returns:
        HTMLResponse: A responsive HTML page containing:
            - API introduction
            - Key features
            - Example endpoint
            - Link to interactive docs
    """
    path = Path("static/home.html")
    return path.read_text(encoding="utf-8")

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    path = Path("static/test.html")
    return path.read_text(encoding="utf-8")

@app.get("/scrape")
async def scrape_aliexpress(product_name: str, top_n: int = 10):
    """
    Scrape and rank AliExpress products based on search query.
    
    Args:
        product_name (str): The product to search for on AliExpress
        top_n (int, optional): Number of top products to return. Defaults to 10.
        
    Returns:
        JSONResponse: Contains either:
            - Success: List of ranked products with:
                - id, title, price, rating, etc.
            - Error: Error message with 500 status code
                
    Raises:
        HTTPException 500: If scraping or ranking fails
    """
    try:
        # Get content of Aliexpress
        scraped_data = await run(product=product_name)

        # Get the best 10 products   
        ranked_data = await rank_products_with_llm(
            search=product_name,
            products=scraped_data,
            top_n=top_n)
        
        return JSONResponse(
            status_code=200,
            content=ranked_data
        )
    except Exception as e:
        ic(f"Scraping error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Product scraping failed", "details": str(e)}
        )
    

# Liba Endpoints

@app.get("/index", response_class=HTMLResponse)
async def index():
    """
    Root endpoint that returns a welcome page with API documentation.
    
    Returns:
        HTMLResponse: A responsive HTML page containing:
            - API introduction
            - Key features
            - Example endpoint
            - Link to interactive docs
    """
    path = Path("static/index.html")
    return path.read_text(encoding="utf-8")

@app.get("/results", response_class=HTMLResponse)
async def results():
    """
    Root endpoint that returns a welcome page with API documentation.
    
    Returns:
        HTMLResponse: A responsive HTML page containing:
            - API introduction
            - Key features
            - Example endpoint
            - Link to interactive docs
    """
    path = Path("static/results.html")
    return path.read_text(encoding="utf-8")