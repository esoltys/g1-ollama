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
            
            if not content.strip():
                return None
            
            # Extract steps from the content
            steps = re.findall(r'\*\*Step \d+: (.+?)\*\*\n(.+?)(?=\n\*\*|\Z)', content, re.DOTALL)
            
            if steps:
                last_step = steps[-1]
                return {
                    "title": last_step[0],
                    "content": last_step[1].strip(),
                    "next_action": "continue" if len(steps) == 1 else "final_answer"
                }
            else:
                return {
                    "title": "Raw Response",
                    "content": content,
                    "next_action": "final_answer" if is_final_answer else "continue"
                }
        
        except Exception as e:
            print(f"Attempt {attempt + 1} failed. Error: {str(e)}")
            if attempt == 2:
                return {
                    "title": "Error",
                    "content": f"Failed to generate {'final answer' if is_final_answer else 'step'} after 3 attempts. Error: {str(e)}",
                    "next_action": "final_answer"
                }
            time.sleep(1)  # Wait for 1 second before retrying

    return None

def generate_response(prompt):
    messages = [
        {"role": "system", "content": """You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Format your response as follows:

**Step 1: [Title]**
[Content]

**Step 2: [Title]**
[Content]

... and so on.

USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES."""},
        {"role": "user", "content": prompt},
    ]
    
    steps = []
    step_count = 1
    total_thinking_time = 0
    
    while True:
        start_time = time.time()
        step_data = make_api_call(messages, 500)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        
        if step_data is None:
            break
        
        steps.append((f"Step {step_count}: {step_data['title']}", step_data['content'], thinking_time))
        
        messages.append({"role": "assistant", "content": json.dumps(step_data)})
        
        if step_data['next_action'] == 'final_answer' or step_data['title'].startswith("Error"):
            break
        
        step_count += 1

        yield steps, None

    if not step_data['title'].startswith("Error"):
        messages.append({"role": "user", "content": "Please provide the final answer based on your reasoning above."})
        
        start_time = time.time()
        final_data = make_api_call(messages, 200, is_final_answer=True)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        
        if final_data:
            steps.append(("Final Answer", final_data['content'], thinking_time))

    yield steps, total_thinking_time

def main():
    st.set_page_config(page_title="g1 prototype", page_icon="🧠", layout="wide")
    
    st.title(f"g1: Using {MODEL_NAME} on Ollama to create o1-like reasoning chains")
    
    st.markdown("""
    This is an early prototype of using prompting to create o1-like reasoning chains to improve output accuracy. It is not perfect and accuracy has yet to be formally evaluated. It is powered by Ollama running locally!
                
    Open source [repository here](https://github.com/bklieger-groq)
    """)
    
    # Text input for user query
    user_query = st.text_input("Enter your query:", placeholder="e.g., How many 'R's are in the word strawberry?")
    
    if user_query:
        st.write("Generating response...")
        
        # Create empty elements to hold the generated text and total time
        response_container = st.empty()
        time_container = st.empty()
        
        # Generate and display the response
        for steps, total_thinking_time in generate_response(user_query):
            with response_container.container():
                for i, (title, content, thinking_time) in enumerate(steps):
                    if title.startswith("Final Answer"):
                        st.markdown(f"### {title}")
                        st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
                    else:
                        with st.expander(title, expanded=True):
                            st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
            
            # Only show total time when it's available at the end
            if total_thinking_time is not None:
                time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

if __name__ == "__main__":
    main()
