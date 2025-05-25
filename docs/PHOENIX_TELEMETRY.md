# Phoenix Telemetry Integration

KitchenCrew now includes integrated observability through [Arize Phoenix](https://phoenix.arize.com/), providing comprehensive tracing and monitoring of your CrewAI agents and LLM interactions.

## What is Phoenix?

Phoenix is an open-source observability platform specifically designed for AI applications. It provides:

- **Trace Visualization**: See the complete flow of your CrewAI agent interactions
- **LLM Monitoring**: Track token usage, latency, and costs across all model calls
- **Performance Analytics**: Identify bottlenecks and optimization opportunities
- **Error Tracking**: Debug issues in your AI workflows
- **Agent Behavior Analysis**: Understand how your agents collaborate and make decisions

## Setup Instructions

### 1. Get Your Phoenix API Key

1. Sign up for a free account at [https://app.phoenix.arize.com](https://app.phoenix.arize.com)
2. Navigate to the "Keys" section in your dashboard
3. Create a new API key for your KitchenCrew project

### 2. Configure Environment Variables

Add your Phoenix API key to your `.env` file:

```bash
# Phoenix Telemetry Configuration
PHOENIX_API_KEY=your_actual_phoenix_api_key_here
```

**Important**: Replace `your_actual_phoenix_api_key_here` with your real API key from Phoenix.

### 3. Verify Installation

The required Phoenix dependencies are already included in the project:
- `arize-phoenix-otel`
- `openinference-instrumentation-crewai`
- `openinference-instrumentation-langchain`
- `openinference-instrumentation-litellm`

### 4. Test the Integration

Run the telemetry status command to verify everything is working:

```bash
# Check telemetry status
uv run python main.py telemetry

# Or from within the chat interface
uv run python main.py chat
# Then type: telemetry
```

## What Gets Traced

When Phoenix tracing is enabled, the following interactions are automatically captured:

### CrewAI Agent Interactions
- Agent task execution and delegation
- Inter-agent communication
- Task completion status and results
- Agent decision-making processes

### LLM Calls
- All OpenAI API calls (GPT-4, GPT-3.5, etc.)
- Prompt templates and variables
- Token usage and costs
- Response times and latency
- Error rates and failures

### Application Flow
- Recipe searches and discoveries
- Meal planning workflows
- Grocery list generation
- Database operations (when relevant to AI tasks)

## Viewing Your Traces

1. **Access Phoenix Dashboard**: Visit [https://app.phoenix.arize.com](https://app.phoenix.arize.com)
2. **Select Your Project**: Look for the "kitchencrew" project
3. **Explore Traces**: View detailed traces of your agent interactions
4. **Analyze Performance**: Use built-in analytics to optimize your workflows

## Privacy and Data Security

- **No Recipe Content**: Your personal recipes and meal plans are not sent to Phoenix
- **Metadata Only**: Only execution metadata, performance metrics, and LLM interactions are traced
- **Secure Transmission**: All data is transmitted securely using HTTPS
- **Data Retention**: Traces are retained according to Phoenix's data retention policies

## Troubleshooting

### Tracing Not Working

1. **Check API Key**: Ensure your `PHOENIX_API_KEY` is set correctly in `.env`
2. **Restart Application**: Phoenix tracing is initialized at startup
3. **Verify Status**: Use the `telemetry` command to check configuration
4. **Check Logs**: Look for Phoenix-related messages in the application logs

### Common Issues

**"Phoenix tracing is disabled"**
- Verify your API key is not a placeholder value
- Ensure the `.env` file is in the project root
- Check that `python-dotenv` is loading the environment variables

**"Failed to initialize Phoenix tracing"**
- Verify internet connectivity
- Check that all Phoenix dependencies are installed
- Review application logs for specific error messages

### Getting Help

If you encounter issues with Phoenix integration:

1. Check the [Phoenix Documentation](https://docs.arize.com/phoenix/)
2. Review the KitchenCrew logs for error messages
3. Use the `telemetry` command to diagnose configuration issues
4. Ensure all dependencies are up to date: `uv sync`

## Benefits for KitchenCrew Users

### Performance Optimization
- Identify slow agent operations
- Optimize LLM prompt efficiency
- Reduce token usage and costs

### Debugging and Development
- Trace complex agent workflows
- Debug failed recipe searches
- Understand agent decision patterns

### Usage Analytics
- Track most-used features
- Monitor application performance
- Identify improvement opportunities

## Example Trace Scenarios

### Recipe Discovery Workflow
```
1. User Query: "find quick italian recipes"
2. Command Parser: Extracts cuisine=italian, max_prep_time=30
3. Recipe Scout Agent: Searches external APIs
4. Recipe Manager Agent: Validates and stores results
5. Response: Formatted recipe list returned to user
```

### Meal Planning Workflow
```
1. User Query: "create a meal plan for this week"
2. Meal Planner Agent: Generates 7-day plan
3. Recipe Manager Agent: Fetches recipe details
4. Database Operations: Stores meal plan
5. Response: Complete meal plan with recipes
```

Each step in these workflows is traced, providing complete visibility into your KitchenCrew operations.

---

**Note**: Phoenix tracing is optional and can be disabled by not setting the `PHOENIX_API_KEY` environment variable. KitchenCrew will function normally without tracing enabled. 