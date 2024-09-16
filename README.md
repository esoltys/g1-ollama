# o1lama
o1lama is a fun experiment designed to enhance the reasoning capabilities of large language models (LLMs) through o1-like reasoning chains. This approach enables the LLM to “think” and solve logical problems that typically challenge leading models. Unlike o1, all reasoning tokens are displayed, and the application utilizes an open-source model running locally on Ollama.

## About
o1lama is an toy project that runs Llama 3.1 **7B** locally using Ollama. It was forked from [https://github.com/bklieger-groq/g1](https://github.com/bklieger-groq/g1) which runs Llama 3.1 **70B** models on groq for speed. This experiment demonstrates the power of prompted reasoning in visualized steps similar in appearance to o1. It obviously is not intended as a comparison to or full replication of o1, which employs different techniques.

## Examples:

### How many 'R's are in the word strawberry?

O1lama gets the wrong answer, but tries to reason. It's interesting that it's blind to the 3rd "r" in Step 3.

![Strawberry example](examples/strawberry.png)

---

### Which is larger, .9 or .11?

O1lama gets this one right.

![0.9 or 0.11 example](examples/math.png)

### Quickstart

1. Ensure you have [Ollama](https://ollama.ai/) installed and running on your system.

2. Pull the Llama-3.1 model (or your preferred model) using Ollama:
   ```
   ollama pull llama3.1
   ```

3. Set up a Python virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

5. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

### Prompting Strategy

The prompt is as follows:

```
You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys. USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Example of a valid JSON response:
```json
{
    "title": "Identifying Key Information",
    "content": "To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...",
    "next_action": "continue"
}```
```

#### Breakdown

First, a persona is added:

> You are an expert AI assistant that explains your reasoning step by step.

Then, instructions to describe the expected step-by-step reasoning process while titling each reasoning step. This includes the ability for the LLM to decide if another reasoning step is needed or if the final answer can be provided.

> For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer.

A specific formatting instruction is provided to ensure consistent output in JSON format:

> Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys.

In all-caps to improve prompt compliance by emphasizing the importance of the instruction, a set of tips and best practices are included.

1. Use as many reasoning steps as possible. At least 3. → This ensures the LLM actually takes the time to think first, and results usually in about 5-10 steps.
2. Be aware of your limitations as an llm and what you can and cannot do. → This helps the LLM remember to use techniques which produce better results, like breaking "strawberry" down into individual letters before counting.
3. Include exploration of alternative answers. Consider you may be wrong, and if you are wrong in your reasoning, where it would be. → A large part of the gains seem to come from the LLM re-evaluating its initial response to ensure it logically aligns with the problem.
4. When you say you are re-examining, actually re-examine, and use another approach to do so. Do not just say you are re-examining. → This encourages the prevention of the LLM just saying it re-examined a problem without actually trying a new approach.
5. Use at least 3 methods to derive the answer. → This helps the LLM come to the right answer by trying multiple methods to derive it.
6. Use best practices. → This is as simple as the "Do better" prompts which improve LLM code output. By telling the LLM to use best practices, or do better, it generally performs better!

### Output Format

The application displays the reasoning process and the final answer in the following format:

1. **Reasoning**: Each reasoning step is shown as an expandable section, with the step title and content.
2. **Answer**: The final answer is displayed after all reasoning steps.
3. **Total thinking time**: The total time taken by the LLM to generate the response is shown at the end.

### Credits

Original g1 app was developed by [Benjamin Klieger](https://x.com/benjaminklieger) which runs Llama 3.1 70B on groq for speed.

Forked for Ollama by [Eric Soltys](https://www.threads.net/@kootenay_eric) to run Llama 3.1 7B locally for fun.
