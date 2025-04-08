from icecream import ic
from typing import List, Dict
import json
from openai import AsyncOpenAI
import os
import time

async def rank_products_with_llm(search: str, products: List[Dict], top_n: int = 10) -> List[Dict]:
    """
    Ranks products using LLM (DeepSeek/OpenAI) with comprehensive debugging.
    
    Args:
        products: List of product dictionaries with AliExpress data
        top_n: Number of top products to return
        
    Returns:
        List of ranked product dictionaries
    """
    
    # --- 1. Initialization ---
    ic.configureOutput(prefix="DEBUG | ", includeContext=True)
    start_time = time.time()
    ic(f"Starting ranking for {len(products)} products")
    
    # --- 2. Data Preprocessing ---
    processed_products = []
    for idx, p in enumerate(products):
        try:
            # Debug: Show raw product
            ic(f"Processing product #{idx}", p.get("id"), p.get("title")[:30] + "...")
            
            # Extract rating (force float)
            rating = float(p.get("rating", 0.0))
            ic("Extracted rating", rating)
            
            # Extract sales from 'trade' field (e.g., "133 sold" → 133)
            sales = 0
            if p.get("trade"):
                try:
                    sales = int(p["trade"].split()[0])
                    ic("Extracted sales", sales)
                except (ValueError, IndexError) as e:
                    ic("Sales extraction error", e, "using 0")
            
            processed_products.append({
                **p,
                "rating": rating,
                "sales": sales  # Add normalized sales count
            })
            
        except Exception as e:
            ic("⚠️ Critical product error", p.get("id"), "|", str(e))
            continue

    # --- 3. Filtering ---
    ic("=== FILTERING ===")
    # Keep products with either positive rating or sales
    valid_products = [
        p for p in processed_products 
        if p["rating"] > 0 or p["sales"] > 0
    ]
    ic(f"Valid products: {len(valid_products)}/{len(products)}")
    
    if not valid_products:
        ic("🚨 No valid products. Falling back to price sorting")
        return sorted(products, key=lambda x: float(x["price"]))[:top_n]

    # --- 4. LLM Ranking (DeepSeek/OpenAI) ---
    if any(p["rating"] >= 4.0 for p in valid_products):
        ic("=== LLM PROCESSING ===")
        try:
            client = AsyncOpenAI(
                api_key=os.getenv("API_KEY"),
                base_url="https://api.deepseek.com"
            )
            
            # Debug: Show prompt template
            prompt = f"""
            Rank these {top_n} products considering:
            1. Rating (prioritize >4.0)
            2. Sales volume ('sales' field)
            3. Price (lower is better)
            4. Very important, make sure the titles of the top 10 products are directly related to the search query and don't show me derivatives, for example: If I ask for a laptop, give me a laptop; if I ask for a laptop accessory, give me a laptop accessory; if I ask for a phone, give me a phone and not its accessories.
                Please, my life depends on it.
                
            Return ONLY JSON with: {{"top_products": [product_list]}}
            
            Products: {valid_products}
            """
            ic("LLM Prompt:", prompt[:500] + "...")  # Show truncated prompt
            
            # API timing
            llm_start = time.time()
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3  # Less randomness
            )
            ic(f"LLM response time: {time.time() - llm_start:.2f}s")
            
            # Debug raw response
            ic("Raw LLM response:", response.choices[0].message.content)
            
            # Strict parsing
            try:
                result = json.loads(response.choices[0].message.content)
                ranked = result.get("top_products", [])[:top_n]
                ic("Ranked products count:", len(ranked))
                return ranked
            except json.JSONDecodeError as e:
                ic("🚨 LLM JSON parse error", e)
                
        except Exception as e:
            ic("🚨 LLM API error", type(e).__name__, str(e))
    
    # --- 5. Local Fallback ---
    ic("=== LOCAL FALLBACK RANKING ===")
    ranked = sorted(
        valid_products,
        key=lambda x: (-x["rating"], -x["sales"], float(x["price"]))  # Higher ratings/sales first, then lower price
    )[:top_n]
    ic("Top local products:", [(p["id"], p["rating"], p["sales"]) for p in ranked])
    
    # --- 6. Final Metrics ---
    ic(f"=== SUMMARY ===")
    ic(f"Total execution: {time.time() - start_time:.2f}s")
    ic(f"Final products: {len(ranked)}")
    
    return ranked


# Example test function
async def test_ranking():
    """Example test case with sample AliExpress data"""
    test_products = [
        {
            "id": "1005008607882755",
            "title": "Egg incubator...",
            "price": 13.09,
            "currency": "USD",
            "trade": "133 sold",
            "rating": 4.8,
            # ... other fields ...
        },
        # ... more test products ...
    ]
    
    ranked = await rank_products_with_llm(test_products)
    print("Final ranked products:", ranked)

# To run: asyncio.run(test_ranking())