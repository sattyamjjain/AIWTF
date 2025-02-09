from setuptools import setup, find_packages

setup(
    name="aiwtf",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "pydantic",
        # Add other dependencies
    ],
    author="AIWTF Team",
    description="A chaotic playground where generative AI, RAG, and rogue AI agents run wild",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
)
