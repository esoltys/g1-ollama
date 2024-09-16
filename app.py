import streamlit as st
import requests
import json
import time
import re

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1"  # Change this to the model you have in Ollama

def make_api_call(messages, max_tokens, is_final_answer=False):
    for attempt in range(3):
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.2
                }
            }
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            
            print(f"Raw API response: {response.text}")
            
            response_json = response.json()
            
            if 'message' not in response_json or 'content' not in response_json['message']:
                raise ValueError(f"Unexpected API response structure: {response_json}")
            
            content = response_json['message']['content']
            
            # Extract all JSON objects from the content
            json_objects = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
            
            parsed_steps = []
            for json_obj in json_objects:
                try:
                    parsed_content = json.loads(json_obj)
                    if isinstance(parsed_content, dict) and all(key in parsed_content for key in ['title', 'content', 'next_action']):
                        parsed_steps.append(parsed_content)
                except json.JSONDecodeError:
                    continue
            
            if parsed_steps:
                return parsed_steps
            
            # If no valid JSON objects found, return an error
            return [{
                "title": "Error",
                "content": "Failed to parse response as JSON",
                "next_action": "final_answer"
            }]
        
        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return [{"title": "Error", "content": f"Failed to generate final answer after 3 attempts. Error: {str(e)}"}]
                else:
                    return [{"title": "Error", "content": f"Failed to generate step after 3 attempts. Error: {str(e)}", "next_action": "final_answer"}]
            time.sleep(1)  # Wait for 1 second before retrying

    return None

def generate_response(prompt):
    messages = [
        {"role": "system", "content": """You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys. USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Example of a valid JSON response:
```json
{
    "title": "Identifying Key Information",
    "content": "To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...",
    "next_action": "continue"
}```
"""},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem."}
    ]
    
    reasoning_steps = []
    step_count = 1
    total_thinking_time = 0
    
    while True:
        start_time = time.time()
        step_data_list = make_api_call(messages, 500)  # Increased token limit
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        
        for step_data in step_data_list:
            reasoning_steps.append((f"Step {step_count}: {step_data['title']}", step_data['content'], thinking_time / len(step_data_list)))
            messages.append({"role": "assistant", "content": json.dumps(step_data)})
            step_count += 1
            
            if step_data['next_action'] == 'final_answer':
                yield reasoning_steps, None, None  # Yield reasoning steps without final answer
                
                # Generate final answer
                messages.append({"role": "user", "content": "Please provide the final answer based on your reasoning above."})
                
                start_time = time.time()
                final_data_list = make_api_call(messages, 200, is_final_answer=True)
                end_time = time.time()
                final_thinking_time = end_time - start_time
                total_thinking_time += final_thinking_time
                
                if final_data_list:
                    final_data = final_data_list[0]  # Take the first (and hopefully only) final answer
                    yield reasoning_steps, ("Final Answer", final_data['content'], final_thinking_time), total_thinking_time
                return

        yield reasoning_steps, None, None  # Yield intermediate steps

    # This line should not be reached, but just in case:
    yield reasoning_steps, None, total_thinking_time


def main():
    st.set_page_config(page_title="o1lama prototype", page_icon="🧠", layout="wide")
    
    st.title(f"o1lama: Using {MODEL_NAME} on Ollama to create o1-like reasoning chains")
    
    st.markdown("""
    This is an early prototype of using prompting to create o1-like reasoning chains to improve output accuracy. It is not perfect and accuracy has yet to be formally evaluated. It is powered by Ollama running locally!
                
    Open source [repository here](https://github.com/esoltys/o1lama)
    """)
    
    # Text input for user query
    user_query = st.text_input("Enter your query:", placeholder="e.g., How many 'R's are in the word strawberry?")
    
    if user_query:
        st.write("Generating response...")
        
        # Create empty elements to hold the generated text and total time
        response_container = st.empty()
        time_container = st.empty()
        
        # Generate and display the response
        for reasoning_steps, final_answer, total_thinking_time in generate_response(user_query):
            with response_container.container():
                st.markdown("### Reasoning")
                for i, (title, content, thinking_time) in enumerate(reasoning_steps):
                    with st.expander(title, expanded=True):
                        st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
                
                if final_answer:
                    st.markdown("### Answer")
                    st.markdown(final_answer[1].replace('\n', '<br>'), unsafe_allow_html=True)
            
            # Only show total time when it's available at the end
            if total_thinking_time is not None:
                time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

if __name__ == "__main__":
    main()
