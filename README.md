# Carlini-Evals

Evaluating code generation capabilities of LLMs (Large Language Models) goes beyond just checking if the code "looks right" — the code must actually be executed and validated against expected outputs. This project benchmarks how well different LLMs perform on real programming problems by:

- Prompting the LLMs with coding tasks.
- Executing their generated code safely using assertions.
- Comparing the actual vs expected outputs to verify correctness.

Each test case is written in a `*.yaml` file, and the evaluations are powered by **Promptfoo**, a framework for testing LLMs.

## What Makes This Evaluation Different?

Unlike traditional benchmarks that rely on human judgment or static analysis, this project uses:
- **Executable Python assertions** for each coding task.
- **Automated scoring** based on real output comparison.
- **Multi-model support** via OpenRouter and OpenAI providers.
- **Flexible configuration**, allowing any subset of tests to be evaluated.

## Evaluation Criteria

LLMs are evaluated based on:

1. **Functional Correctness** – Does the generated code produce the right output?
2. **Execution Robustness** – Does it run without errors?
3. **Prompt Compliance** – Does it follow instructions closely?

---

## 🔧 Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nitin399-maker/carlini_evals.git
   cd carlini_evals
   $env:OPENROUTER_API_KEY=...
   $env:LLMFOUNDRY_TOKEN=.....
   $env:PROMPTFOO_PYTHON_ENCODING = "utf-8"
   
   # Run 3 specific test cases
    npx promptfoo eval -c file1.yaml -c file2.yaml -c file2.yaml --no-cache
    
    # Run all test cases that match a naming pattern (for example)
    npx promptfoo eval -c "merge-*.yaml"
    npx promptfoo eval -c "*-parsing.yaml"

   # Run multiple or all YAMLs using glob pattern
   npx promptfoo eval -c "*.yaml"
