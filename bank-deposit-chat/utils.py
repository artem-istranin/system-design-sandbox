import os

def validate_required_env_vars():
    required_env_vars = [
        'LANGSMITH_API_KEY',
        'ANTHROPIC_API_KEY',
        'TAVILY_API_KEY'
    ]
    missing_vars = [var for var in required_env_vars if var not in os.environ]
    if missing_vars:
        missing = ', '.join(missing_vars)
        raise EnvironmentError(f"Missing required environment variables: {missing}")