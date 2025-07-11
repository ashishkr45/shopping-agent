# AI Shopping Assistant 🛒🤖

An intelligent terminal-based shopping assistant that helps you find the best products within your budget. The assistant uses Google Gemini AI and web scraping to search across multiple e-commerce platforms and provide personalized product recommendations.

## Features ✨

- **Natural Language Processing**: Enter queries in plain English (e.g., "I want to buy a gaming laptop with RTX 4060 under 150k")
- **Multi-Platform Search**: Searches across Flipkart and Amazon India
- **AI-Powered Analysis**: Uses Google Gemini to analyze and rank products
- **Budget-Aware**: Only shows products within your specified budget
- **Detailed Recommendations**: Provides top 3 products with explanations
- **Terminal Interface**: Clean, easy-to-use command-line interface

## How It Works 🔄

1. **Query Parsing**: AI extracts product name and budget from your natural language query
2. **Web Scraping**: Searches Flipkart and Amazon for matching products
3. **Filtering**: Filters products based on your budget constraints
4. **AI Analysis**: Gemini AI analyzes and ranks products based on relevance, ratings, and value
5. **Recommendations**: Returns top 3 products with detailed explanations

## Installation 🚀

### Prerequisites

- Python 3.8+
- Google API Key (for Gemini AI)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-shopping-assistant
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

4. **Create environment file**:
Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your_google_api_key_here
```

### Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key to your `.env` file

## Usage 💡

### Basic Usage

Run the application:
```bash
python main.py
```

### Example Queries

- `"I want to buy a smartphone under 30k with good camera"`
- `"Looking for gaming laptop with RTX 4060 under 150000"`
- `"Need wireless headphones below 5000"`
- `"Best tablet under 25k for students"`
- `"Gaming chair under 20000"`

### Sample Output

```
🤖 AI Shopping Assistant
==================================================
💬 Your query: I want to buy a gaming laptop with RTX 4060 under 150000

🔍 Parsing your query...
📱 Product: gaming laptop RTX 4060
💰 Budget: ₹150,000

🛒 Searching for products...
  📦 Searching Flipkart...
  ✅ Found 8 products from Flipkart
  📦 Searching Amazon...
  ✅ Found 5 products from Amazon
  ✅ Total products found: 13

🤖 Analyzing products...

🎯 TOP RECOMMENDATIONS:
==================================================

1. ASUS TUF Gaming A15 (2023) AMD Ryzen 5 7535HS 15.6" (40.64 cms) FHD 144Hz, RTX 4060, 16GB DDR5, 512GB SSD
   💰 Price: ₹89,990
   ⭐ Rating: 4.3
   🛒 Source: Flipkart
   💡 Why recommended: Excellent value for money with RTX 4060 and high refresh rate display
   🔗 Link: https://www.flipkart.com/asus-tuf-gaming-a15-2023...
--------------------------------------------------
```

## Project Structure 📁

```
ai-shopping-assistant/
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── README.md              # This file
└── .gitignore            # Git ignore file
```

## Dependencies 📦

The project uses the following key libraries:

- **Google Generative AI**: For AI-powered query parsing and product analysis
- **Playwright**: For web scraping e-commerce sites
- **LangGraph**: For creating AI agent workflows
- **LangChain**: For message handling and AI integration
- **AsyncIO**: For asynchronous operations
- **Python-dotenv**: For environment variable management

## Configuration ⚙️

### Environment Variables

Create a `.env` file with:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### Supported E-commerce Sites

Currently supports:
- **Flipkart** (flipkart.com)
- **Amazon India** (amazon.in)

## Features in Detail 🔍

### Natural Language Processing
- Extracts product specifications from natural language
- Understands budget formats (30k, 50000, etc.)
- Handles complex queries with multiple requirements

### Web Scraping
- **Anti-bot measures**: Realistic browser simulation
- **Dynamic content**: Handles JavaScript-loaded content
- **Fallback selectors**: Multiple CSS selectors for reliability
- **Rate limiting**: Respectful scraping practices

### AI Analysis
- **Relevance scoring**: Matches products to user intent
- **Value analysis**: Price-to-feature ratio evaluation
- **Rating consideration**: Customer satisfaction metrics
- **Detailed explanations**: Why each product is recommended

## Troubleshooting 🔧

### Common Issues

1. **No products found**:
   - Check your internet connection
   - Try simplifying your search query
   - Increase your budget range

2. **API errors**:
   - Verify your Google API key is correct
   - Check API quota limits
   - Ensure the API key has Gemini access

3. **Scraping failures**:
   - Sites may have updated their structure
   - Check if sites are accessible
   - Try running again after some time

### Debug Mode

For detailed logging, modify the script to include debug prints:
```python
# Add this at the top of main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitations ⚠️

- **Rate limiting**: Respectful scraping means slower searches
- **Site changes**: E-commerce sites may update their structure
- **Regional availability**: Currently optimized for Indian e-commerce sites
- **Product availability**: Real-time stock may vary

## Future Enhancements 🚀

- [ ] Add more e-commerce sites (Myntra, Paytm Mall, etc.)
- [ ] Price tracking and alerts
- [ ] Product comparison features
- [ ] Review sentiment analysis
- [ ] Export recommendations to CSV/PDF
- [ ] GUI interface
- [ ] Price history tracking

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 🆘

If you encounter any issues:

1. Check the troubleshooting section
2. Ensure all dependencies are installed correctly
3. Verify your API key is valid
4. Check if the e-commerce sites are accessible

## Disclaimer ⚖️

This tool is for educational and personal use only. Please respect the terms of service of the e-commerce websites being scraped. The authors are not responsible for any misuse of this tool.

## Acknowledgments 🙏

- Google Gemini AI for intelligent analysis
- Playwright team for excellent web automation tools
- LangChain & LangGraph for AI workflow management
- E-commerce platforms for providing product data

---

**Happy Shopping! 🛒✨**