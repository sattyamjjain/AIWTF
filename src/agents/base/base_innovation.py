from typing import TypedDict, Annotated, Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
import operator
from .base_agent import BaseAgent


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    context: Dict[str, Any]
    artifacts: Dict[str, Any]


class BaseInnovationAgent(BaseAgent):
    """Base class for innovation-focused agents"""

    def __init__(self, tools: List[Any], system_prompt: str):
        super().__init__(tools=tools, system_prompt=system_prompt)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
                ("ai", "{agent_scratchpad}"),
            ]
        )

        # Create the agent
        self._agent = create_openai_functions_agent(
            llm=self.llm, tools=tools, prompt=prompt
        )

        # Create agent executor
        self._agent_executor = AgentExecutor(
            agent=self._agent, tools=tools, verbose=True, handle_parsing_errors=True
        )

        # Initialize state graph
        self.workflow = self._create_workflow(system_prompt)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

    def _create_workflow(self, system_prompt: str) -> StateGraph:
        """Create the agent's workflow graph."""
        # Initialize graph
        builder = StateGraph(AgentState)

        # Add nodes
        builder.add_node("process_input", self._process_input)
        builder.add_node("execute_tools", self._execute_tools)
        builder.add_node("generate_response", self._generate_response)

        # Set entry point
        builder.set_entry_point("process_input")

        # Add edges
        builder.add_conditional_edges(
            "process_input",
            self._should_use_tools,
            {"use_tools": "execute_tools", "generate": "generate_response"},
        )
        builder.add_edge("execute_tools", "generate_response")
        builder.add_conditional_edges(
            "generate_response",
            self._should_continue,
            {"continue": "process_input", "end": END},
        )

        return builder.compile()

    def _process_input(self, state: AgentState) -> AgentState:
        """Process the input and update state."""
        return state

    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used."""
        return "use_tools" if self.tools else "generate"

    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute the required tools."""
        return state

    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate the final response."""
        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine if the workflow should continue."""
        return "end"

    async def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the agent with the given input."""
        result = await self._agent_executor.ainvoke({"input": input_text, **kwargs})

        return {
            "response": result["output"],
            "artifacts": result.get("intermediate_steps", []),
        }

    async def aclose(self):
        """Close async resources"""
        await super().aclose()
