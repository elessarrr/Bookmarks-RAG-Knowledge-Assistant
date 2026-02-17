# Universal Knowledge Compounder

A universal, IDE-agnostic Python tool that automates the "Compounding Knowledge" workflow. It analyzes your daily git changes, extracts learnings using an LLM (OpenAI or Ollama), and documents them in your repository.

## Features
- **IDE Agnostic:** Works with Trae, VS Code, Cursor, Zed, or any terminal.
- **Provider Support:** Plug-and-play support for OpenAI (GPT-4) and Ollama (Local Llama 3).
- **Automated Reporting:** Generates markdown reports of your daily achievements and pitfalls.

## Installation

```bash
pip install .
```

## Usage

### 1. Run Manually (CLI)
Navigate to your project root and run:

```bash
# Use OpenAI (Requires OPENAI_API_KEY env var)
compound run --provider openai

# Use Local Ollama
compound run --provider ollama --model llama3
```

### 2. Integration with Trae
Add a task to your workflow or simply run the terminal command within Trae's terminal.

### 3. Nightly Automation (Cron)
Add this to your crontab to run at 11:30 PM:

```bash
30 23 * * * cd /path/to/your/project && compound run --provider openai >> compound.log 2>&1
```

## Configuration
The tool uses environment variables for sensitive keys:
- `OPENAI_API_KEY`: Required for OpenAI provider.

## License
MIT
