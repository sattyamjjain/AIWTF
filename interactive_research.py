import asyncio
from src.innovations.research.agent import ResearchAgent
import logging
from dotenv import load_dotenv
import os
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler

# Set up console
console = Console()

# Configure logging
logging.basicConfig(
    level="ERROR",  # Only show errors by default
    format="%(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True, markup=True, show_time=False, show_path=False)
    ],
)

# Disable other loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Load environment variables
load_dotenv(override=True)  # Add override=True to ensure variables are reloaded

# Verify API keys
serpapi_key = os.getenv("SERPAPI_API_KEY")
if not serpapi_key:
    raise ValueError("SERPAPI_API_KEY not found in environment variables")
print(f"Using SerpAPI key: {serpapi_key[:8]}...")

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")


# Test SerpAPI key
def test_serpapi():
    from serpapi import GoogleSearch

    try:
        search = GoogleSearch(
            {"api_key": serpapi_key, "engine": "google", "q": "test", "num": 1}
        )
        results = search.get_dict()
        if "error" in results:
            raise ValueError(f"SerpAPI error: {results['error']}")
        print("SerpAPI key is valid!")
    except Exception as e:
        print(f"SerpAPI key test failed: {str(e)}")
        raise


# Test the API key before starting
test_serpapi()


def print_research_results(result: Dict[str, Any]):
    """Print research results in a structured format"""

    # Print header
    console.print("\n")
    console.print(
        Panel(
            f"[bold blue]Research Results: {result['topic']}[/bold blue]", expand=False
        )
    )

    # Print Summary
    console.print("\n[bold cyan]📋 Summary[/bold cyan]")
    console.print(Panel(result["summary"], border_style="cyan"))

    # Print Key Findings
    console.print("\n[bold green]🔑 Key Findings[/bold green]")
    for category, points in result["key_findings"].items():
        if points:
            console.print(f"\n[bold]{category}[/bold]")
            for point in points:
                console.print(f"  • {point}")

    # Print Statistics
    if any(v for v in result["statistics"].values()):
        console.print("\n[bold yellow]📊 Statistics and Data[/bold yellow]")
        stats_table = Table(show_header=True, header_style="bold yellow")
        stats_table.add_column("Category")
        stats_table.add_column("Data Points")

        for category, stats in result["statistics"].items():
            if stats:
                stats_formatted = "\n".join(f"• {stat}" for stat in stats)
                stats_table.add_row(category, stats_formatted)

        console.print(stats_table)

    # Print Sources
    if result["sources"]:
        console.print("\n[bold magenta]📚 Sources[/bold magenta]")
        sources_table = Table(show_header=False, box=None)
        for source in result["sources"]:
            sources_table.add_row(
                f"• [bold]{source['title']}[/bold]",
            )
            sources_table.add_row(
                f"  [blue]{source['url']}[/blue]",
            )
        console.print(sources_table)

    # Print Metadata
    console.print("\n[bold]📌 Research Metadata[/bold]")
    metadata_table = Table(show_header=False, box=None)
    metadata_table.add_row("Depth", str(result["metadata"]["depth"]))
    metadata_table.add_row("Sources analyzed", str(result["metadata"]["source_count"]))
    metadata_table.add_row("Duration", str(result["metadata"]["duration"]))

    if result["metadata"]["errors"]:
        metadata_table.add_row(
            "[bold red]Errors[/bold red]",
            "\n".join(f"• {error}" for error in result["metadata"]["errors"]),
        )

    console.print(metadata_table)
    console.print("\n" + "=" * 50 + "\n")


async def interactive_research():
    """Interactive research interface"""

    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] OPENAI_API_KEY not found in environment variables"
        )
        return

    if not os.getenv("SERPAPI_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] SERPAPI_API_KEY not found in environment variables"
        )
        return

    agent = ResearchAgent()

    while True:
        # Get topic from user
        topic = console.input("\nEnter research topic (or 'quit' to exit): ")
        if topic.lower() == "quit":
            break

        # Get research depth
        try:
            depth = int(console.input("Enter research depth (1-3): "))
            depth = max(1, min(3, depth))  # Clamp between 1 and 3
        except ValueError:
            depth = 1
            console.print("[yellow]Invalid depth, using default of 1[/yellow]")

        try:
            with console.status("[bold green]Researching...[/bold green]"):
                result = await agent.research_topic(
                    topic=topic, depth=depth, max_sources=5
                )

            print_research_results(result)

        except Exception as e:
            console.print(f"[bold red]Research failed:[/bold red] {str(e)}")


if __name__ == "__main__":
    # Test API keys
    console.print("[bold]Initializing research system...[/bold]")

    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key:
        console.print(f"[green]✓[/green] Using SerpAPI key: {serpapi_key[:8]}...")
    else:
        console.print("[red]✗[/red] SERPAPI_API_KEY not found")

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        console.print(f"[green]✓[/green] OpenAI API key found")
    else:
        console.print("[red]✗[/red] OPENAI_API_KEY not found")

    console.print()

    asyncio.run(interactive_research())
