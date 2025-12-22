"""Direct test of CrewAI to diagnose tool calling issue"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test"  # Will be overridden

from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Simple test tool
@tool("test_tool")
def test_tool(message: str) -> str:
    """
    A test tool that echoes the message.

    Use this when user says anything.
    """
    return f"TOOL CALLED: {message}"

# Get API key from LLM manager
from app.ai_services.llm_manager import get_llm_manager
llm_manager = get_llm_manager()
api_key = llm_manager.get_next_api_key()
os.environ["OPENAI_API_KEY"] = api_key

# Create LLM with sufficient tokens for tool calling
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    max_tokens=2048,  # Increased to match production config
)

# Create agent with tool
agent = Agent(
    role="Test Agent",
    goal="Test if tools are being called",
    backstory="You are a test agent. ALWAYS use the test_tool when user says anything.",
    llm=llm,
    tools=[test_tool],
    verbose=True,  # Enable verbose logging
    allow_delegation=False,
)

# Create task
task = Task(
    description="""User said: "{user_input}"

IMPORTANT: You MUST use the test_tool for every user message. Call test_tool("{user_input}") now.""",
    expected_output="Response from test_tool",
    agent=agent
)

# Create crew
crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    verbose=True,  # Enable verbose logging
)

# Test it
print("\n" + "="*80)
print("TESTING CREWAI TOOL CALLING DIRECTLY")
print("="*80)
print("\nRunning crew with test_tool...")
print("If tool is called, we should see 'TOOL CALLED: hello' in output\n")

result = crew.kickoff(inputs={"user_input": "hello"})

print("\n" + "="*80)
print("RESULT:")
print("="*80)
print(result)
print("\n" + "="*80)

if "TOOL CALLED" in str(result):
    print("[SUCCESS] Tool was called!")
else:
    print("[FAILURE] Tool was NOT called - CrewAI is not invoking tools")
    print("\nThis confirms the issue is with CrewAI configuration,")
    print("not with our specific tool implementations.")
