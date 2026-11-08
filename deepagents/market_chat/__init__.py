"""Chat application of the market analysis agent.

Modules:
- config: paths, model name and prompts.
- schema: structured answer of the skill.
- run_log: log file and link extraction helpers.
- middleware: RunLogMiddleware, which logs each step and collects links.
- report: Markdown rendering of the answer.
- agent: creation of the deep agent.
- session: the interactive chat loop.
"""
