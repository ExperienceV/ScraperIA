from icecream import ic
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from functions.aliexpress_scraper import run
from functions.llm_integration import rank_products_with_llm

app = FastAPI(
    title="AliExpress Scraper API",
    description="API for scraping and ranking AliExpress products using AI",
    version="1.0.0"
)

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
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AliExpress Scraper API</title>
    <style>
        :root {
            --primary-color: #ff6f00;
            --secondary-color: #ffab40;
            --dark-color: #333;
            --light-color: #f5f5f5;
            --success-color: #4caf50;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: var(--light-color);
            color: var(--dark-color);
        }
        
        .container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        header {
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 1rem;
        }
        
        h1 {
            color: var(--primary-color);
            margin: 0;
        }
        
        .logo {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .api-info {
            background-color: #f9f9f9;
            padding: 1.5rem;
            border-radius: 6px;
            margin: 1.5rem 0;
        }
        
        .endpoint {
            background-color: var(--light-color);
            padding: 1rem;
            border-left: 4px solid var(--primary-color);
            margin: 1rem 0;
            font-family: monospace;
        }
        
        .btn {
            display: inline-block;
            background-color: var(--primary-color);
            color: white;
            padding: 0.7rem 1.5rem;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
            font-weight: bold;
            margin-top: 1rem;
        }
        
        .btn:hover {
            background-color: var(--secondary-color);
        }
        
        footer {
            text-align: center;
            margin-top: 2rem;
            color: #666;
            font-size: 0.9rem;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-top: 3px solid var(--primary-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🛍️</div>
            <h1>AliExpress Scraper API</h1>
            <p>Powerful product scraping and ranking API service</p>
        </header>
        
        <div class="api-info">
            <h2>API Endpoint</h2>
            <div class="endpoint">
                GET /scrape?product_name={product_name}&top_n={results_count}
            </div>
            <a href="/docs" class="btn">View API Documentation</a>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <h3>Real-time Data</h3>
                <p>Get fresh product data directly from AliExpress with every request.</p>
            </div>
            <div class="feature-card">
                <h3>Smart Ranking</h3>
                <p>AI-powered product ranking based on ratings, sales, and price.</p>
            </div>
            <div class="feature-card">
                <h3>Easy Integration</h3>
                <p>Simple REST API that works with any programming language.</p>
            </div>
        </div>
        
        <footer>
            <p>© 2025 AliExpress Scraper API | Powered by FastAPI</p>
        </footer>
    </div>
</body>
</html>
    """

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