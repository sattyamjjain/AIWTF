from setuptools import setup, find_packages

setup(
    name="aiwtf",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    author="AIWTF Team",
    description="A chaotic playground where generative AI, RAG, and rogue AI agents run wild",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
)
