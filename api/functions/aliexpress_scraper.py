
from parsel import Selector
from typing import Dict
import asyncio 
import math
from icecream import ic
import httpx
import json
ic.disable()

def extract_search(response) -> Dict:
    """extract json data from search page"""
    sel = Selector(response.text)
    # find script with result.pagectore data in it._it_t_=
    script_with_data = sel.xpath('//script[contains(.,"_init_data_=")]')
    # select page data from javascript variable in script tag using regex
    data = json.loads(script_with_data.re(r'_init_data_\s*=\s*{\s*data:\s*({.+}) }')[0])
    return data['data']['root']['fields']

def parse_search(response):
    """Parse search page response for product preview results"""
    data = extract_search(response)
    parsed = []
    for result in data["mods"]["itemList"]["content"]:
        parsed.append(
            {
                "id": result["productId"],
                "url": f"https://www.aliexpress.com/item/{result['productId']}.html",
                "type": result["productType"],  # can be either natural or ad
                "title": result["title"]["displayTitle"],
                "price": result["prices"]["salePrice"]["minPrice"],
                "currency": result["prices"]["salePrice"]["currencyCode"],
                "trade": result.get("trade", {}).get("tradeDesc"),  # trade line is not always present
                "rating": result.get("evaluation", {}).get("starRating", 0.0),
                "thumbnail": result["image"]["imgUrl"].lstrip("/"),
                "store": {
                    "url": result["store"]["storeUrl"],
                    "name": result["store"]["storeName"],
                    "id": result["store"]["storeId"],
                    "ali_id": result["store"]["aliMemberId"],
                },
            }
        )
    return parsed

async def scrape_search(query: str, session: httpx.AsyncClient, sort_type="default", max_pages: int = None):
    """Scrape all search results and return parsed search result data"""
    query = query.replace(" ", "+")

    async def scrape_search_page(page):
        """Scrape a single aliexpress search page and return all embedded JSON search data"""
        print(f"scraping search query {query}:{page} sorted by {sort_type}")
        resp = await session.get(
            "https://www.aliexpress.com/wholesale?trafficChannel=main"
            f"&d=y&CatId=0&SearchText={query}&ltype=wholesale&SortType={sort_type}&page={page}"
        )
        return resp

    # scrape first search page and find total result count
    first_page = await scrape_search_page(1)
    first_page_data = extract_search(first_page)
    page_size = first_page_data["pageInfo"]["pageSize"]
    total_pages = int(math.ceil(first_page_data["pageInfo"]["totalResults"] / page_size))
    if total_pages > 60:
        print(f"query has {total_pages}; lowering to max allowed 60 pages")
        total_pages = 60

    # get the number of total pages to scrape
    if max_pages and max_pages < total_pages:
        total_pages = max_pages

    # scrape remaining pages concurrently
    print(f'scraping search "{query}" of total {total_pages} sorted by {sort_type}')

    other_pages = await asyncio.gather(*[scrape_search_page(page=i) for i in range(1, total_pages + 1)])
    for response in [first_page, *other_pages]:
        product_previews = []
        product_previews.extend(parse_search(response))

    return product_previews

async def run(product: str = "iphone 14"):
    client = httpx.AsyncClient(follow_redirects=True)
    data = await scrape_search(query=product, session=client, max_pages=1)
    #data_json = json.dumps(data, indent=2, ensure_ascii=False)
    ic(f"Productos obtenidos: {data}")
    return data
