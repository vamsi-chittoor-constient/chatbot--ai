"""Simplified CrewAI tool calling test - no app dependencies"""
import os
import sys

# Add app to path to import llm_manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'restaurant-chatbot'))

from app.ai_services.llm_manager import get_llm_manager

# Get valid API key from LLM manager
llm_manager = get_llm_manager()
api_key = llm_manager.get_next_api_key()
os.environ["OPENAI_API_KEY"] = api_key
print(f"✓ Using API key from LLM manager: {api_key[:20]}...")


from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Simple test tool
@tool("test_tool")
def test_tool(message: str) -> str:
    """
    A test tool that echoes the message.
    
    Use this when user says anything.
    
    Args:
        message: The message to echo
        
    Returns:
        Echoed message with prefix
    """
    print(f"✅ TOOL CALLED: {message}")
    return f"TOOL EXECUTED: {message}"

# Create LLM with INCREASED max_tokens
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.environ["OPENAI_API_KEY"],
    max_tokens=2048,  # INCREASED from 512
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
print("TESTING CREWAI TOOL CALLING - SIMPLIFIED VERSION")
print("="*80)
print(f"LLM Config: model=gpt-4o-mini, max_tokens=2048")
print(f"Tools: 1 tool (test_tool)")
print("="*80)
print("\nRunning crew with test_tool...")
print("If tool is called, we should see '✅ TOOL CALLED: hello' in output\n")

try:
    result = crew.kickoff(inputs={"user_input": "hello"})
    
    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(result)
    print("\n" + "="*80)
    
    if "TOOL EXECUTED" in str(result) or "TOOL CALLED" in str(result):
        print("✅ [SUCCESS] Tool was called!")
        print("\nFIX CONFIRMED: Increasing max_tokens from 512 to 2048 solved the issue!")
    else:
        print("❌ [FAILURE] Tool was NOT called")
        print("\nPossible issues:")
        print("1. CrewAI version incompatibility")
        print("2. LLM not configured for function calling")
        print("3. Tool schema generation issue")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
