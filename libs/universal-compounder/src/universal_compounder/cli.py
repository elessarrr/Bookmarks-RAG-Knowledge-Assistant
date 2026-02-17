import click
from .engine import CompoundEngine
import os

@click.group()
def cli():
    """Universal Knowledge Compounder Tool"""
    pass

@cli.command()
@click.option('--provider', default='openai', help='LLM Provider (openai/ollama)')
@click.option('--model', default=None, help='Model name')
@click.option('--output', default='docs/knowledge', help='Output directory for reports')
def run(provider, model, output):
    """Run the nightly compound review."""
    
    # Defaults
    if not model:
        if provider == 'openai':
            model = 'gpt-4-turbo-preview'
        elif provider == 'ollama':
            model = 'llama3'

    engine = CompoundEngine(provider=provider, model=model, output_dir=output)
    engine.run_nightly_review()

if __name__ == '__main__':
    cli()
