import logging
from base_test_case import BaseAsyncTestCase
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama


MCP_SERVER_URL="http://localhost:8000/sse"
OLLAMA_URL="http://localhost:11434"


class TestMcpServer(BaseAsyncTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        logging.info('Test setup')
        self._llm = ChatOllama(model="qwen3:8b", base_url=OLLAMA_URL, reasoning=True, temperature=0)
        self._client = MultiServerMCPClient(
            {
                "Demo": {
                    "url": MCP_SERVER_URL,
                    "transport": "sse",
                }
            }
        )

    async def asyncTearDown(self):
        await super().asyncTearDown()
        logging.info('Test teardown')

    # This method runs once before any test methods in this class
    @classmethod
    def setUpClass(cls):
        pass

    # This method runs once after all test methods in this class
    @classmethod
    def tearDownClass(cls):
        pass

    async def test_mcp(self):
        logging.info('Testing basic mcp server functionality')
        tools = await self._client.get_tools()

        agent = create_react_agent(
            self._llm,
            tools
        )

        resp = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What health care providers are available in our clinic and what are their roles?"}]}
        )

        logging.info(f'Tool call response :{resp}')
        is_ok = 'Susan Davis'.lower() in resp['messages'][-1].content.lower()
        self.assertTrue(is_ok)

        resp = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "When is Susan Davis open for bookings? Provide a list of open time slots."}]}
        )
        is_ok = '#### **August 16, 2024**'.lower() in resp['messages'][-1].content.lower()
        self.assertTrue(is_ok)


if __name__ == "__main__":
    unittest.main()
