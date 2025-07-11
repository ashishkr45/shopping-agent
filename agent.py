import asyncio
import json
import re
from typing import Dict, List, Any, TypedDict, Annotated
from urllib.parse import quote_plus
import google.generativeai as genai
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    product_name: str
    budget: float
    scraped_products: List[Dict[str, Any]]
    final_recommendations: List[Dict[str, Any]]

class ProductScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_flipkart(self, search_term: str, budget: float) -> List[Dict]:
        """Scrape Flipkart products with improved URL extraction"""
        page = await self.context.new_page()
        
        try:
            query = quote_plus(search_term)
            url = f"https://www.flipkart.com/search?q={query}&sort=price_asc"
            
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            products = []
            
            # Try multiple selectors for Flipkart product cards
            selectors = [
                "[data-id]",
                "._1AtVbE",
                "._13oc-S",
                "._1fQZEK",
                ".s1Q9rs",
                "._2kHMtA"
            ]
            
            product_cards = None
            for selector in selectors:
                try:
                    product_cards = page.locator(selector)
                    count = await product_cards.count()
                    if count > 0:
                        print(f"Found {count} product cards with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not product_cards or await product_cards.count() == 0:
                print("No Flipkart products found")
                return []
            
            card_count = await product_cards.count()
            for i in range(min(card_count, 20)):
                try:
                    card = product_cards.nth(i)
                    product_info = await self.extract_flipkart_product_info(card)
                    
                    if product_info and product_info.get('price') is not None:
                        if product_info['price'] <= budget:
                            product_info['source'] = 'Flipkart'
                            products.append(product_info)
                
                except Exception as e:
                    print(f"Error extracting product {i}: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Flipkart scraping error: {e}")
            return []
        finally:
            await page.close()
    
    async def extract_flipkart_product_info(self, card):
        """Extract product information from Flipkart product card with improved URL extraction"""
        product_info = {
            'title': None,
            'rating': None,
            'price': None,
            'reviews_count': None,
            'brand': None,
            'mrp': None,
            'discount': None,
            'url': None
        }
        
        try:
            # Improved URL extraction for Flipkart
            link_selectors = [
                "a[href*='/p/']",
                "a[title]",
                "a[href]",
                "._1fQZEK",
                ".s1Q9rs",
                "._4rR01T",
                "._2WkVRV"
            ]
            
            for selector in link_selectors:
                try:
                    link_elements = card.locator(selector)
                    count = await link_elements.count()
                    
                    for i in range(count):
                        try:
                            link_element = link_elements.nth(i)
                            relative_url = await link_element.get_attribute('href')
                            
                            if relative_url and ('/p/' in relative_url or '/dp/' in relative_url):
                                if relative_url.startswith('/'):
                                    product_info['url'] = f"https://www.flipkart.com{relative_url}"
                                elif relative_url.startswith('http'):
                                    product_info['url'] = relative_url
                                else:
                                    product_info['url'] = f"https://www.flipkart.com/{relative_url}"
                                break
                        except Exception:
                            continue
                    
                    if product_info['url']:
                        break
                except Exception:
                    continue
            
            # Extract title with improved selectors
            title_selectors = [
                "._4rR01T",
                ".s1Q9rs",
                "._2WkVRV", 
                ".IRpwTa",
                "a[title]",
                "._1fQZEK",
                "a span",
                "div[title]"
            ]
            
            for selector in title_selectors:
                try:
                    title_elements = card.locator(selector)
                    count = await title_elements.count()
                    
                    for i in range(min(count, 3)):
                        try:
                            title_element = title_elements.nth(i)
                            title_text = await title_element.inner_text()
                            
                            if not title_text:
                                title_text = await title_element.get_attribute('title')
                            
                            if title_text:
                                title_text = title_text.strip()
                                if len(title_text) > 10:
                                    product_info['title'] = title_text
                                    break
                        except Exception:
                            continue
                    
                    if product_info['title']:
                        break
                except Exception:
                    continue
            
            # Extract price with improved logic
            price_selectors = [
                "._30jeq3",
                "._1_WHN1",
                "._3tbHP2",
                "._1vC4OE",
                "._30jeq3._1_WHN1",
                ".CEmiEU",
                "._1_WHN1._30jeq3"
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = card.locator(selector)
                    count = await price_elements.count()
                    
                    for i in range(count):
                        try:
                            price_element = price_elements.nth(i)
                            price_text = await price_element.inner_text()
                            
                            if price_text:
                                price_text = price_text.strip()
                                # Remove currency symbols and extract numbers
                                price_match = re.search(r'₹?(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
                                if price_match:
                                    price_str = price_match.group(1).replace(',', '')
                                    try:
                                        price_value = float(price_str)
                                        if price_value > 100:  # Reasonable minimum
                                            product_info['price'] = price_value
                                            break
                                    except ValueError:
                                        continue
                        except Exception:
                            continue
                    
                    if product_info['price']:
                        break
                except Exception:
                    continue
            
            # Extract rating
            rating_selectors = [
                "._3LWZlK",
                "._3LWZlK div",
                "._3LWZlK span",
                "[class*='rating']",
                "._13vcmD"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = card.locator(selector).first
                    if await rating_element.count() > 0:
                        rating_text = await rating_element.inner_text()
                        if rating_text:
                            rating_text = rating_text.strip()
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                rating_value = float(rating_match.group(1))
                                if 0 <= rating_value <= 5:
                                    product_info['rating'] = rating_value
                                    break
                except Exception:
                    continue
            
            # Set default rating if not found
            if product_info['rating'] is None:
                product_info['rating'] = "N/A"
            
            # Debug logging
            if product_info['title'] and product_info['price']:
                print(f"Flipkart Product: {product_info['title'][:50]}... | Price: ₹{product_info['price']} | URL: {product_info['url']}")
            
            return product_info if product_info['title'] and product_info['price'] else None
            
        except Exception as e:
            print(f"Error extracting Flipkart product info: {e}")
            return None
    
    async def scrape_amazon(self, product_name: str, budget: float) -> List[Dict[str, Any]]:
        """Scrape products from Amazon with improved URL extraction"""
        page = await self.context.new_page()
        
        try:
            # Search for products
            search_query = product_name.replace(" ", "+")
            url = f"https://www.amazon.in/s?k={search_query}"
            
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector("div[data-component-type='s-search-result']", timeout=15000)
            await page.wait_for_timeout(2000)
            
            products = []
            product_cards = page.locator("div[data-component-type='s-search-result']")
            
            card_count = await product_cards.count()
            print(f"Found {card_count} Amazon product cards")
            
            for i in range(min(card_count, 20)):
                try:
                    card = product_cards.nth(i)
                    product_info = await self.extract_amazon_product_info(card)
                    
                    if product_info and product_info.get('price') is not None:
                        if product_info['price'] <= budget:
                            product_info['source'] = 'Amazon'
                            products.append(product_info)
                
                except Exception as e:
                    print(f"Error extracting Amazon product {i}: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Amazon scraping error: {e}")
            return []
        finally:
            await page.close()
    
    async def extract_amazon_product_info(self, card):
        """Extract product information from Amazon product card with improved URL extraction"""
        product_info = {
            'title': None,
            'rating': None,
            'price': None,
            'reviews_count': None,
            'brand': None,
            'mrp': None,
            'discount': None,
            'url': None
        }
        
        try:
            # Improved URL extraction for Amazon
            link_selectors = [
                "h2 a[href]",
                "a[href*='/dp/']",
                "a[href*='/gp/product/']",
                ".a-link-normal[href]",
                "a[data-component-type='s-product-image']",
                ".s-image[href]"
            ]
            
            for selector in link_selectors:
                try:
                    link_elements = card.locator(selector)
                    count = await link_elements.count()
                    
                    for i in range(count):
                        try:
                            link_element = link_elements.nth(i)
                            relative_url = await link_element.get_attribute('href')
                            
                            if relative_url and ('/dp/' in relative_url or '/gp/product/' in relative_url):
                                if relative_url.startswith('/'):
                                    product_info['url'] = f"https://www.amazon.in{relative_url}"
                                elif relative_url.startswith('http'):
                                    product_info['url'] = relative_url
                                else:
                                    product_info['url'] = f"https://www.amazon.in/{relative_url}"
                                break
                        except Exception:
                            continue
                    
                    if product_info['url']:
                        break
                except Exception:
                    continue
            
            # Extract title
            title_selectors = [
                "div[data-cy='title-recipe'] h2.a-size-base-plus span",
                "div[data-cy='title-recipe'] h2 span",
                "h2.a-size-mini a span",
                "h2.a-size-mini span",
                "h2 a span",
                "h2 span",
                ".a-size-base-plus",
                ".a-size-medium"
            ]
            
            for selector in title_selectors:
                try:
                    title_elements = card.locator(selector)
                    element_count = await title_elements.count()
                    
                    for i in range(min(element_count, 3)):
                        try:
                            title_element = title_elements.nth(i)
                            title_text = await title_element.inner_text()
                            
                            if title_text:
                                title_text = title_text.strip()
                                if len(title_text) > 10:
                                    product_info['title'] = title_text
                                    break
                        except Exception:
                            continue
                    
                    if product_info['title']:
                        break
                except Exception:
                    continue
            
            # Extract rating
            rating_selectors = [
                "span[aria-label*='out of 5 stars']",
                "span.a-icon-alt",
                "div[data-cy='reviews-block'] span.a-size-small.a-color-base",
                ".a-icon-alt"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = card.locator(selector).first
                    if await rating_element.count() > 0:
                        rating_text = await rating_element.inner_text()
                        if not rating_text:
                            rating_text = await rating_element.get_attribute('aria-label') or ""
                        
                        if rating_text:
                            rating_text = rating_text.strip()
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                rating_value = float(rating_match.group(1))
                                if 0 <= rating_value <= 5:
                                    product_info['rating'] = rating_value
                                    break
                except Exception:
                    continue
            
            # Extract price
            price_selectors = [
                "span.a-price span.a-offscreen",
                "span.a-price-whole",
                ".a-price .a-offscreen",
                ".a-price-range .a-price .a-offscreen",
                ".a-price"
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = card.locator(selector)
                    element_count = await price_elements.count()
                    
                    for i in range(element_count):
                        try:
                            price_element = price_elements.nth(i)
                            price_text = await price_element.inner_text()
                            
                            if price_text:
                                price_text = price_text.strip()
                                # Remove currency symbols and extract numbers
                                price_match = re.search(r'₹?(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
                                if price_match:
                                    price_str = price_match.group(1).replace(',', '')
                                    try:
                                        price_value = float(price_str)
                                        if price_value > 100:  # Reasonable minimum
                                            product_info['price'] = price_value
                                            break
                                    except ValueError:
                                        continue
                        except Exception:
                            continue
                    
                    if product_info['price']:
                        break
                except Exception:
                    continue
            
            # Set default rating if not found
            if product_info['rating'] is None:
                product_info['rating'] = "N/A"
            
            return product_info if product_info['title'] and product_info['price'] else None
            
        except Exception as e:
            print(f"Error extracting Amazon product info: {e}")
            return None

class ShoppingAgent:
    def __init__(self):
        # Configure Google Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.llm = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.scraper = ProductScraper()
        self.graph = self.create_graph()
        
    def create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_query", self.parse_query)
        workflow.add_node("scrape_products", self.scrape_products)
        workflow.add_node("analyze_products", self.analyze_products)
        
        # Add edges
        workflow.add_edge("parse_query", "scrape_products")
        workflow.add_edge("scrape_products", "analyze_products")
        workflow.add_edge("analyze_products", END)
        
        # Set entry point
        workflow.set_entry_point("parse_query")
        
        return workflow.compile()
    
    async def parse_query(self, state: AgentState) -> AgentState:
        """Parse user query to extract product name and budget"""
        print("🔍 Parsing your query...")
        
        prompt = f"""
        You are a shopping assistant. Extract the product name and budget from the user's query.
        
        Return your response in this exact JSON format:
        {{
            "product_name": "extracted product name",
            "budget": extracted_budget_as_number
        }}
        
        Examples:
        - "I want to buy a smartphone under 30k with good camera" -> {{"product_name": "smartphone with good camera", "budget": 30000}}
        - "Looking for laptop under 50000" -> {{"product_name": "laptop", "budget": 50000}}
        - "Need headphones below 5k" -> {{"product_name": "headphones", "budget": 5000}}
        
        Convert k to thousands (30k = 30000).
        If no budget is mentioned, assume a reasonable budget based on the product type.
        
        User query: {state["user_query"]}
        """
        
        try:
            response = await asyncio.to_thread(self.llm.generate_content, prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                state["product_name"] = parsed_data["product_name"]
                state["budget"] = float(parsed_data["budget"])
                
                print(f"📱 Product: {state['product_name']}")
                print(f"💰 Budget: ₹{state['budget']:,.0f}")
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing query: {e}")
            # Fallback extraction
            budget_match = re.search(r'(\d+)k?', state["user_query"], re.IGNORECASE)
            if budget_match:
                budget = float(budget_match.group(1))
                if 'k' in state["user_query"].lower():
                    budget *= 1000
                state["budget"] = budget
            else:
                state["budget"] = 50000  # Default budget
                
            state["product_name"] = state["user_query"]
        
        return state
    
    async def scrape_products(self, state: AgentState) -> AgentState:
        """Scrape products from e-commerce sites"""
        print("🛒 Searching for products...")
        
        await self.scraper.initialize()
        
        all_products = []
        
        # Scrape from Flipkart
        print("  📦 Searching Flipkart...")
        try:
            flipkart_products = await self.scraper.scrape_flipkart(
                state["product_name"], 
                state["budget"]
            )
            all_products.extend(flipkart_products)
            print(f"  ✅ Found {len(flipkart_products)} products from Flipkart")
        except Exception as e:
            print(f"  ❌ Flipkart search failed: {e}")
        
        # Scrape from Amazon
        print("  📦 Searching Amazon...")
        try:
            amazon_products = await self.scraper.scrape_amazon(
                state["product_name"], 
                state["budget"]
            )
            all_products.extend(amazon_products)
            print(f"  ✅ Found {len(amazon_products)} products from Amazon")
        except Exception as e:
            print(f"  ❌ Amazon search failed: {e}")
        
        await self.scraper.close()
        
        state["scraped_products"] = all_products
        print(f"  ✅ Total products found: {len(all_products)}")
        
        return state
    
    async def analyze_products(self, state: AgentState) -> AgentState:
        """Analyze and rank products using LLM"""
        print("🤖 Analyzing products...")
        
        if not state["scraped_products"]:
            state["final_recommendations"] = []
            return state
        
        # Prepare products for analysis
        products_for_analysis = []
        for product in state["scraped_products"]:
            products_for_analysis.append({
                "name": product["title"],
                "price": product["price"],
                "rating": product["rating"],
                "url": product["url"],
                "source": product["source"]
            })
        
        products_json = json.dumps(products_for_analysis, indent=2)
        
        prompt = f"""
        You are a product recommendation expert. Analyze the following products and recommend the top 3 that best match the user's query: "{state['user_query']}"
        
        Consider these factors:
        1. Relevance to the search query
        2. Price-to-value ratio
        3. Customer ratings (if available)
        4. Product features mentioned in the name
        
        Products data:
        {products_json}
        
        Return your response as a JSON array of the top 3 products with explanations:
        [
            {{
                "rank": 1,
                "name": "product name",
                "price": price_number,
                "rating": "rating_value",
                "url": "product_url",
                "source": "source_name",
                "why_recommended": "brief explanation why this product is recommended"
            }}
        ]
        
        If there are fewer than 3 products, return all available products.
        Make sure to preserve the original URLs from the input data.
        """
        
        try:
            response = await asyncio.to_thread(self.llm.generate_content, prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                state["final_recommendations"] = recommendations
            else:
                # Fallback: sort by rating and price
                sorted_products = sorted(
                    products_for_analysis,
                    key=lambda x: (-(x["rating"] if isinstance(x["rating"], (int, float)) else 0), x["price"])
                )
                
                # Format as recommendations
                recommendations = []
                for i, product in enumerate(sorted_products[:3], 1):
                    recommendations.append({
                        "rank": i,
                        "name": product["name"],
                        "price": product["price"],
                        "rating": product["rating"],
                        "url": product["url"],
                        "source": product["source"],
                        "why_recommended": f"Ranked #{i} based on price and rating"
                    })
                
                state["final_recommendations"] = recommendations
                
        except Exception as e:
            print(f"Error analyzing products: {e}")
            # Fallback to top 3 by price
            sorted_products = sorted(state["scraped_products"], key=lambda x: x["price"])
            recommendations = []
            for i, product in enumerate(sorted_products[:3], 1):
                recommendations.append({
                    "rank": i,
                    "name": product["title"],
                    "price": product["price"],
                    "rating": product["rating"],
                    "url": product["url"],
                    "source": product["source"],
                    "why_recommended": f"Ranked #{i} by price"
                })
            state["final_recommendations"] = recommendations
        
        return state
    
    def format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations for display"""
        if not recommendations:
            return "❌ No products found within your budget. Try increasing your budget or modifying your search."
        
        output = "\n🎯 TOP RECOMMENDATIONS:\n" + "="*50 + "\n"
        
        for i, product in enumerate(recommendations, 1):
            output += f"\n{i}. {product['name']}\n"
            output += f"   💰 Price: ₹{product['price']:,.0f}\n"
            output += f"   ⭐ Rating: {product['rating']}\n"
            output += f"   🛒 Source: {product['source']}\n"
            
            if 'why_recommended' in product:
                output += f"   💡 Why recommended: {product['why_recommended']}\n"
            
            if product.get('url') and product['url'] != 'None':
                output += f"   🔗 Link: {product['url']}\n"
            else:
                output += f"   🔗 Link: URL not available\n"
            
            output += "-" * 50 + "\n"
        
        return output
    
    async def process_query(self, user_query: str) -> str:
        """Process user query and return recommendations"""
        initial_state = AgentState(
            messages=[],
            user_query=user_query,
            product_name="",
            budget=0.0,
            scraped_products=[],
            final_recommendations=[]
        )
        
        try:
            # Run the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Format and return recommendations
            return self.format_recommendations(result["final_recommendations"])
            
        except Exception as e:
            return f"❌ Error processing your request: {str(e)}"

async def main():
    """Main function to run the terminal chatbot"""
    print("🤖 AI Shopping Assistant")
    print("=" * 50)
    print("Enter your product query (e.g., 'I want to buy a smartphone under 30k with good camera')")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key in the .env file")
        return
    
    agent = ShoppingAgent()
    
    while True:
        try:
            query = input("\n💬 Your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for using AI Shopping Assistant!")
                break
            
            if not query:
                continue
            
            print("\n" + "="*50)
            
            # Process the query
            result = await agent.process_query(query)
            print(result)
            
        except KeyboardInterrupt:
            print("\n👋 Thanks for using AI Shopping Assistant!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())