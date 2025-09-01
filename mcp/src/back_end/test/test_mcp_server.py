import logging
from base_test_case import BaseAsyncTestCase
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from util.settings import OLLAMA_URL, MCP_SERVER_URL


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
        self._tools = await self._client.get_tools()
        self._prompt_coroutine = await self._client.get_prompt('Demo', 'configure_assistant')
        self._prompt = self._prompt_coroutine[0].content

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

        agent = create_react_agent(
            self._llm,
            self._tools,
            prompt=self._prompt
        )

        resp = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What health care providers are available in our clinic and what are their roles?"}]}
        )

        logging.info(f'Tool call response :{resp}')
        is_ok = 'Susan Davis'.lower() in resp['messages'][-1].content.lower()
        self.assertTrue(is_ok)

        resp = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "I want to book an apointment with Susan Davis ? Find the 5 earliest times."}]}
        )
        logging.info(f'Tool call response :{resp}')
        is_ok = '2024-08-07 12:00:00'.lower() in resp['messages'][-1].content.lower()
        self.assertTrue(is_ok)


if __name__ == "__main__":
    unittest.main()
