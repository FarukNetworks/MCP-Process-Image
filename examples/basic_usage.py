"""Basic usage example for the MCP Image Processing Server."""

import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    """Example of using the image processing MCP server."""

    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_process_image.server"],
        env={
            "OPENAI_API_KEY": "your_openai_api_key_here"  # Replace with your actual API key
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # List available resources
            resources = await session.list_resources()
            print("\nAvailable resources:")
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.description}")

            # Example: Process an image
            try:
                result = await session.call_tool(
                    "process_image",
                    {
                        "image_source": "https://example.com/image.jpg",  # Replace with actual image
                        "api_provider": "openai",
                        "analysis_type": "comprehensive",
                    },
                )
                print(f"\nImage analysis result: {result.content}")
            except Exception as e:
                print(f"Error processing image: {e}")

            # Example: Extract text from image
            try:
                result = await session.call_tool(
                    "extract_text",
                    {
                        "image_source": "path/to/image/with/text.jpg",  # Replace with actual image
                        "api_provider": "openai",
                    },
                )
                print(f"\nText extraction result: {result.content}")
            except Exception as e:
                print(f"Error extracting text: {e}")

            # Example: Get API capabilities
            try:
                capabilities = await session.read_resource("config://api-capabilities")
                print(f"\nAPI capabilities: {capabilities}")
            except Exception as e:
                print(f"Error getting capabilities: {e}")


if __name__ == "__main__":
    asyncio.run(main())
