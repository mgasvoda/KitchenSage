# Web Tools OpenAI Integration

## Overview

The KitchenCrew web tools have been updated to use OpenAI's Responses API with web search capabilities, replacing the previous placeholder implementations. This provides real-time web search and intelligent content extraction for recipe discovery.

## Updated Tools

### 1. WebSearchTool

**Purpose**: Searches the web for recipes using OpenAI's web search functionality.

**Key Features**:
- Real-time web search using OpenAI's `gpt-4o-mini` model
- Structured recipe data extraction
- Automatic URL generation for web scraping
- JSON response parsing with fallback text parsing
- Enhanced prompts to ensure recipe-specific results

**Usage**:
```python
from src.tools.web_tools import WebSearchTool

search_tool = WebSearchTool()
results = search_tool._run("quick vegetarian pasta recipes", max_results=5)
```

**Response Format**:
```json
[
  {
    "name": "Recipe Name",
    "source": "website.com",
    "url": "https://website.com/recipe/recipe-name",
    "ingredients": ["ingredient1", "ingredient2"],
    "instructions": ["step1", "step2"],
    "prep_time": 15,
    "cook_time": 20,
    "total_time": 35,
    "servings": 4,
    "difficulty": "Easy",
    "tags": ["vegetarian", "quick"],
    "nutrition": {
      "calories": 300,
      "protein": 12,
      "carbs": 45,
      "fat": 8
    }
  }
]
```

### 2. WebScrapingTool

**Purpose**: Scrapes and extracts structured recipe data from cooking websites using AI.

**Key Features**:
- AI-powered content extraction from recipe URLs
- Structured data parsing
- Fallback text parsing when JSON extraction fails
- Metadata tracking (scraping timestamp)
- Error handling and graceful degradation

**Usage**:
```python
from src.tools.web_tools import WebScrapingTool

scraping_tool = WebScrapingTool()
results = scraping_tool._run("https://allrecipes.com/recipe/example", search_terms="vegetarian")
```

## Integration Workflow

The tools work together in a two-step process:

1. **WebSearchTool** finds recipes and provides URLs
2. **WebScrapingTool** extracts detailed content from those URLs

```python
# Step 1: Search for recipes
search_tool = WebSearchTool()
search_results = search_tool._run("italian pasta recipes")

# Step 2: Scrape detailed content from found URLs
scraping_tool = WebScrapingTool()
for recipe in search_results:
    if 'url' in recipe:
        detailed_recipe = scraping_tool._run(recipe['url'])
        # Process detailed recipe data
```

## Configuration

### Environment Variables

Ensure your `.env` file contains:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Model Configuration

Both tools use `gpt-4o-mini` as specified in the requirements. This can be modified in the tool initialization:

```python
response = client.responses.create(
    model="gpt-4o-mini",  # Can be changed to other supported models
    input=enhanced_prompt,
    tools=[{"type": "web_search_preview"}]
)
```

## Error Handling

The tools include comprehensive error handling:

1. **API Key Validation**: Checks for OpenAI API key availability
2. **Network Errors**: Handles connection and timeout issues
3. **Parsing Errors**: Fallback mechanisms for malformed responses
4. **Content Extraction**: Graceful degradation when content cannot be parsed

## Testing

Run the test script to verify functionality:

```bash
uv run python test_web_search.py
```

The test script will:
- Verify OpenAI API key configuration
- Test web search functionality
- Test web scraping capabilities
- Provide detailed output and error reporting

## CrewAI Agent Integration

The updated tools integrate seamlessly with CrewAI agents:

```python
from src.agents.recipe_scout import RecipeScoutAgent

# The RecipeScoutAgent automatically uses the updated tools
scout = RecipeScoutAgent()
# Tools are available as scout.tools[0] (WebSearchTool) and scout.tools[1] (WebScrapingTool)
```

## Prompt Engineering

### WebSearchTool Prompt Structure

The tool uses an enhanced prompt to ensure recipe-specific results:

```python
enhanced_prompt = f"""
Search for {query} recipes and provide detailed recipe information. 
For each recipe found, please include:
1. Recipe name
2. Source website URL (this is crucial for web scraping)
3. Ingredients list
4. Cooking instructions
5. Prep time, cook time, and total time
6. Servings
7. Difficulty level
8. Any dietary tags (vegetarian, vegan, gluten-free, etc.)
9. Nutrition information if available

Please format the response as a JSON array of recipe objects...
"""
```

### WebScrapingTool Prompt Structure

The scraping tool uses targeted prompts for content extraction:

```python
scraping_prompt = f"""
Please scrape the recipe content from this URL: {url}

Extract the following information and format it as a JSON object:
1. Recipe name
2. Complete ingredients list with quantities
3. Step-by-step cooking instructions
4. Prep time, cook time, and total time
5. Number of servings
6. Difficulty level
7. Dietary tags (vegetarian, vegan, gluten-free, etc.)
8. Nutrition information if available
9. Recipe description or summary
10. Any cooking tips or notes
"""
```

## Performance Considerations

1. **Rate Limiting**: OpenAI API has rate limits - implement appropriate delays for bulk operations
2. **Caching**: Consider caching search results to avoid redundant API calls
3. **Batch Processing**: For multiple URLs, implement batch processing with error handling
4. **Cost Management**: Monitor API usage as web search operations consume tokens

## Future Enhancements

1. **Caching Layer**: Implement Redis or local caching for frequently searched recipes
2. **Batch Operations**: Support for bulk recipe discovery and scraping
3. **Source Filtering**: Allow filtering by trusted recipe sources
4. **Image Extraction**: Extract recipe images from scraped content
5. **Nutrition Analysis**: Enhanced nutrition data extraction and validation

## Troubleshooting

### Common Issues

1. **API Key Not Found**:
   - Ensure `OPENAI_API_KEY` is set in your `.env` file
   - Verify the API key is valid and has sufficient credits

2. **No Results Returned**:
   - Check internet connectivity
   - Verify the search query is recipe-related
   - Try different search terms

3. **JSON Parsing Errors**:
   - The tools include fallback text parsing
   - Check the OpenAI response format in logs

4. **Scraping Failures**:
   - Some websites may block automated access
   - The tool provides graceful error handling
   - Try alternative URLs from search results

### Debug Mode

Enable verbose logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your web tool operations
```

## API Reference

### WebSearchTool._run()

```python
def _run(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the web for recipes using OpenAI's web search.
    
    Args:
        query: Search query for recipes
        max_results: Maximum number of results to return
        
    Returns:
        List of recipe search results with URLs for scraping
    """
```

### WebScrapingTool._run()

```python
def _run(self, url: str, search_terms: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scrape recipes from a website using OpenAI for content extraction.
    
    Args:
        url: Website URL to scrape
        search_terms: Optional search terms to filter results
        
    Returns:
        List of scraped recipes with structured data
    """
```

---

*Last Updated: Web tools successfully integrated with OpenAI Responses API*
*Status: ✅ Ready for production use* 