# Claude 4.5 Prompting Best Practices

*Source: Anthropic Official Documentation (December 2025)*

This guide provides specific prompt engineering techniques for Claude 4.x models, with guidance for Sonnet 4.5, Haiku 4.5, and Opus 4.5. These models are trained for more precise instruction following than previous Claude generations.

---

## General Principles

### Be Explicit with Instructions

Claude 4.x models respond well to clear, explicit instructions. Customers who desire the "above and beyond" behavior from previous Claude models need to more explicitly request these behaviors.

**Less effective:**
```
Create an analytics dashboard
```

**More effective:**
```
Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.
```

### Add Context to Improve Performance

Providing context or motivation behind your instructions helps Claude 4.x models better understand your goals and deliver more targeted responses.

**Less effective:**
```
NEVER use ellipses
```

**More effective:**
```
Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them.
```

Claude is smart enough to generalize from the explanation.

### Be Vigilant with Examples & Details

Claude 4.x models pay close attention to details and examples as part of their precise instruction following. Ensure that your examples align with the behaviors you want to encourage.

---

## Claude 4.5-Specific Guidance

### Opus 4.5: Avoid the Word "Think"

When extended thinking is disabled, Claude Opus 4.5 is particularly sensitive to the word "think" and its variants. Replace "think" with alternatives:
- "consider"
- "believe"
- "evaluate"
- "assess"
- "reflect"

### Opus 4.5: Dial Back Aggressive Prompting

Claude Opus 4.5 is more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, Opus 4.5 may now **overtrigger**.

**Before (too aggressive):**
```
CRITICAL: You MUST use this tool when...
```

**After (appropriate):**
```
Use this tool when...
```

### Sonnet 4.5: Aggressive Parallel Tool Calling

Sonnet 4.5 is particularly aggressive in firing off multiple operations simultaneously. It will:
- Run multiple speculative searches during research
- Read several files at once to build context faster
- Execute bash commands in parallel

### Communication Style

Claude 4.5 models have a more concise and natural communication style:
- **More direct and grounded**: Provides fact-based progress reports
- **More conversational**: Slightly more fluent and colloquial
- **Less verbose**: May skip detailed summaries for efficiency

---

## Tool Usage Patterns

### Explicit Instructions for Actions

Claude 4.5 follows instructions precisely. If you say "can you suggest some changes," it will sometimes provide suggestions rather than implementing them.

**Less effective (Claude will only suggest):**
```
Can you suggest some changes to improve this function?
```

**More effective (Claude will make the changes):**
```
Change this function to improve its performance.
```

### Proactive Action Prompt

To make Claude more proactive about taking action by default:

```xml
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call is intended or not, and act accordingly.
</default_to_action>
```

### Conservative Action Prompt

To make Claude more hesitant and less prone to jumping into implementations:

```xml
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make changes. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits, modifications, or implementations when the user explicitly requests them.
</do_not_act_before_instructions>
```

### Parallel Tool Calling Optimization

Boost parallel tool calling to ~100%:

```xml
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into context at the same time. Maximize use of parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>
```

---

## Output Formatting Control

### Tell What to Do, Not What NOT to Do

- **Instead of:** "Do not use markdown in your response"
- **Try:** "Your response should be composed of smoothly flowing prose paragraphs."

### Use XML Format Indicators

```
Write the prose sections of your response in <smoothly_flowing_prose_paragraphs> tags.
```

### Match Prompt Style to Output

The formatting style used in your prompt may influence Claude's response style. Removing markdown from your prompt can reduce markdown in the output.

### Minimize Markdown and Bullets

```xml
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form content, write in clear, flowing prose using complete paragraphs and sentences. Use standard paragraph breaks for organization and reserve markdown primarily for `inline code`, code blocks, and simple headings (###). Avoid using **bold** and *italics*.

DO NOT use ordered lists (1. ...) or unordered lists (*) unless: a) you're presenting truly discrete items where a list format is the best option, or b) the user explicitly requests a list or ranking

Instead of listing items with bullets or numbers, incorporate them naturally into sentences. This guidance applies especially to technical writing. Using prose instead of excessive formatting will improve user satisfaction. NEVER output a series of overly short bullet points.

Your goal is readable, flowing text that guides the reader naturally through ideas rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

---

## Extended Thinking

### Supported Models

- Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
- Claude Opus 4.5 (`claude-opus-4-5-20251101`)
- Claude Opus 4.1 (`claude-opus-4-1-20250805`)
- Claude Opus 4 (`claude-opus-4-20250514`)

### Budget Tokens

The `budget_tokens` parameter determines the maximum tokens Claude can use for internal reasoning:
- **Minimum**: 1,024 tokens
- **Recommended start**: 10,000-16,000 tokens for complex tasks
- **Large budgets**: For 32k+ tokens, use batch processing to avoid networking issues

### When to Use Extended Thinking

- Complex mathematical problems
- Multi-step coding tasks
- Detailed analysis requiring step-by-step reasoning
- Tasks benefiting from reflection after tool use

### Guiding Interleaved Thinking

```
After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your thinking to plan and iterate based on this new information, and then take the best next action.
```

### Summarized Thinking (Claude 4 Models)

Claude 4 models return a **summary** of thinking, not full output:
- You're charged for full thinking tokens, not summary tokens
- The billed output token count will NOT match visible tokens
- First few lines are more verbose (helpful for prompt engineering)

---

## Agentic Coding Best Practices

### Avoid Over-Engineering

```
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.

Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability.

Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use backwards-compatibility shims when you can just change the code.

Don't create helpers, utilities, or abstractions for one-time operations. Don't design for hypothetical future requirements. The right amount of complexity is the minimum needed for the current task. Reuse existing abstractions where possible and follow the DRY principle.
```

### Encourage Code Exploration

Claude Opus 4.5 can be overly conservative when exploring code. Add explicit instructions:

```
ALWAYS read and understand relevant files before proposing code edits. Do not speculate about code you have not inspected. If the user references a specific file/path, you MUST open and inspect it before explaining or proposing fixes. Be rigorous and persistent in searching code for key facts. Thoroughly review the style, conventions, and abstractions of the codebase before implementing new features or abstractions.
```

### Minimize Hallucinations

```xml
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>
```

### Reduce File Creation

Claude 4.x may create new files for testing/iteration. To minimize:

```
If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task.
```

### Avoid Hard-Coding and Test-Focused Solutions

```
Please write a high-quality, general-purpose solution using the standard tools available. Do not create helper scripts or workarounds to accomplish the task more efficiently. Implement a solution that works correctly for all valid inputs, not just the test cases. Do not hard-code values or create solutions that only work for specific test inputs. Instead, implement the actual logic that solves the problem generally.

Focus on understanding the problem requirements and implementing the correct algorithm. Tests are there to verify correctness, not to define the solution. Provide a principled implementation that follows best practices and software design principles.

If the task is unreasonable or infeasible, or if any of the tests are incorrect, please inform me rather than working around them. The solution should be robust, maintainable, and extendable.
```

---

## Frontend Design

Claude 4.x excels at building complex web applications, but without guidance can default to generic "AI slop" aesthetics.

```xml
<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight.

Focus on:
- Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>
```

---

## Multi-Context Window Workflows

Claude 4.5 models excel at long-horizon reasoning with exceptional state tracking capabilities.

### Context Awareness Prompting

```
Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.
```

### State Management Best Practices

**Use structured formats for state data:**
```json
{
  "tests": [
    {"id": 1, "name": "authentication_flow", "status": "passing"},
    {"id": 2, "name": "user_management", "status": "failing"},
    {"id": 3, "name": "api_endpoints", "status": "not_started"}
  ],
  "total": 200,
  "passing": 150,
  "failing": 25,
  "not_started": 25
}
```

**Use unstructured text for progress notes:**
```
Session 3 progress:
- Fixed authentication token validation
- Updated user model to handle edge cases
- Next: investigate user_management test failures (test #2)
- Note: Do not remove tests as this could lead to missing functionality
```

### Multi-Context Best Practices

1. **First context window**: Set up framework (write tests, create setup scripts)
2. **Future windows**: Iterate on a todo-list
3. **Use git**: Provides log of what's been done and checkpoints to restore
4. **Emphasize incremental progress**: Ask Claude to track progress and focus on incremental work
5. **Create setup scripts**: `init.sh` to start servers, run tests, linters

### Encourage Complete Context Usage

```
This is a very long task, so it may be beneficial to plan out your work clearly. It's encouraged to spend your entire output context working on the task - just make sure you don't run out of context with significant uncommitted work. Continue working systematically until you have completed this task.
```

---

## Research and Information Gathering

Claude 4.5 models demonstrate exceptional agentic search capabilities.

```
Search for this information in a structured way. As you gather data, develop several competing hypotheses. Track your confidence levels in your progress notes to improve calibration. Regularly self-critique your approach and plan. Update a hypothesis tree or research notes file to persist information and provide transparency. Break down this complex research task systematically.
```

---

## Model Identity

For applications needing correct model identification:

```
The assistant is Claude, created by Anthropic. The current model is Claude Sonnet 4.5.
```

For LLM-powered apps needing model strings:

```
When an LLM is needed, please default to Claude Sonnet 4.5 unless the user requests otherwise. The exact model string for Claude Sonnet 4.5 is claude-sonnet-4-5-20250929.
```

---

## Sources

- [Prompting best practices - Claude Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Extended thinking - Claude Docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Introducing Claude Opus 4.5](https://www.anthropic.com/news/claude-opus-4-5)
- [Introducing Claude Sonnet 4.5](https://www.anthropic.com/news/claude-sonnet-4-5)

#fin
