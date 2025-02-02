from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from typing import List, Union, Any
import os
from openai import AsyncOpenAI, OpenAI
import backoff
import logging

logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(
        self,
        tools: List[Any],
        system_prompt: str,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        # Initialize OpenAI clients with API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.openai_client = OpenAI(api_key=api_key)
        self.async_openai_client = AsyncOpenAI(api_key=api_key)

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            client=self.openai_client,
            async_client=self.async_openai_client,
            streaming=True,
            max_retries=max_retries,
            request_timeout=30,
        )

        self.tools = tools
        self.system_prompt = system_prompt

        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, output_key="output"
        )

        default_prompt = """You are a helpful AI assistant that can use tools to accomplish tasks.
        Always think through tasks step by step and explain your reasoning.
        If you're not sure about something, ask for clarification."""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt or default_prompt),
                ("human", "{input}"),
                ("ai", "{agent_scratchpad}"),
            ]
        )

        self.agent = create_openai_functions_agent(
            llm=self.llm, tools=tools, prompt=self.prompt
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
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
            response = await self.agent_executor.ainvoke({"input": input_text})
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
