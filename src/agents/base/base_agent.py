from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Union, Any, Optional, Callable, Awaitable
import os
from openai import AsyncOpenAI, OpenAI
import backoff
import logging
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import asyncio

logger = logging.getLogger(__name__)

def make_async_tool(tool: BaseTool) -> Tool:
    """Convert a BaseTool into a Tool with proper async handling"""
    if hasattr(tool, '_arun'):
        async_func = tool._arun
    elif hasattr(tool, '_run'):
        async_func = tool._run
    else:
        raise ValueError(f"Tool {tool.name} must have either _run or _arun method")
    
    return Tool(
        name=tool.name,
        description=tool.description,
        func=async_func,
        return_direct=getattr(tool, 'return_direct', False)
    )

class BaseAgent:
    """Base agent class with common functionality"""

    def __init__(self, tools: List[Union[Tool, BaseTool]], system_prompt: str):
        """Initialize the base agent"""
        # Convert tools to proper format
        self.tools = [
            make_async_tool(tool) if isinstance(tool, BaseTool) else tool
            for tool in tools
        ]

        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Create the chat prompt template for OpenAI functions agent
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Initialize OpenAI clients with API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.openai_client = OpenAI(api_key=api_key)
        self.async_openai_client = AsyncOpenAI(api_key=api_key)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Create the OpenAI functions agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            return_intermediate_steps=True,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

    @backoff.on_exception(backoff.expo, (Exception), max_tries=3, max_time=30)
    async def run(self, input_text: str) -> str:
        """Run the agent on input text with retries"""
        try:
            response = await self.agent_executor.ainvoke({
                "input": input_text,
                "agent_scratchpad": "",  # Initialize empty scratchpad
                "chat_history": []  # Initialize empty chat history
            })
            return response["output"]
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return f"Error: {str(e)}"

    async def aclose(self):
        """Close async resources"""
        try:
            await self.async_openai_client.close()
            self.openai_client.close()
        except Exception as e:
            logger.error(f"Error closing clients: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.aclose()
