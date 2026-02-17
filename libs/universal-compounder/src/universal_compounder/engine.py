import os
from datetime import datetime
from .llm_adapter import LLMProvider, get_provider
from .git_utils import get_recent_changes
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT

class CompoundEngine:
    def __init__(self, provider: str = "openai", output_dir: str = "docs/knowledge", **kwargs):
        self.llm = get_provider(provider, **kwargs)
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def run_nightly_review(self):
        """Runs the nightly review process."""
        print("Starting nightly review...")
        
        # 1. Get Changes
        print("Fetching recent git changes...")
        changes = get_recent_changes(hours=24)
        if "No changes found" in changes:
            print("No changes to process.")
            return

        # 2. Analyze with LLM
        print("Analyzing changes with LLM...")
        prompt = SUMMARY_PROMPT.format(git_history=changes)
        report = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        # 3. Save Report
        filename = f"daily-report-{datetime.now().strftime('%Y-%m-%d')}.md"
        path = os.path.join(self.output_dir, filename)
        
        with open(path, "w") as f:
            f.write(report)
        
        print(f"Report saved to {path}")
        return path
