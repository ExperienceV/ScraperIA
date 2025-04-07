from icecream import ic
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api.functions.aliexpress_scraper import run
from api.functions.llm_integration import rank_products_with_llm

app = FastAPI()

@app.get("/scrape")
async def scrape_aliexpress(product_name: str):
    try:
        # Get content of Aliexpress
        scraped_data = await run(product=product_name)

        # Get the best 10 products   
        ranked_data = await rank_products_with_llm(scraped_data)
        
        return JSONResponse(
            status_code=200,
            content=ranked_data
        )
    except Exception as e:
        ic(str(e))