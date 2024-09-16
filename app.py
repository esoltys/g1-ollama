import streamlit as st
import requests
import json
import time
import re

OLLAMA_API_URL = "http://localhost:11434/api/chat"

def get_available_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models = response.json()["models"]
        return [model["name"] for model in models]
    except Exception as e:
        st.error(f"Failed to fetch models: {str(e)}")
        return ["llama3.1"]  # Return default model if fetching fails

def make_api_call(messages, max_tokens, model_name, is_final_answer=False):
    for attempt in range(3):
        try:
            payload = {
                "model": model_name,
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
            done_reason = response_json.get('done_reason', None)
            
            # Parse the multi-step response
            steps = re.split(r'(### Step \d+:.*?|### Final Answer:.*?)(?=\n)', content)
            steps = [step.strip() for step in steps if step.strip()]
            
            parsed_steps = []
            for i in range(0, len(steps), 2):
                if i + 1 < len(steps):
                    title = steps[i]
                    content = steps[i+1]
                    
                    if "Final Answer:" in title:
                        next_action = "final_answer"
                    else:
                        next_action = "continue"
                    
                    parsed_steps.append({
                        "title": title,
                        "content": content,
                        "next_action": next_action
                    })
            
            # If we found valid steps, return them along with done_reason
            if parsed_steps:
                return parsed_steps, done_reason
            
            # If no valid steps found, create a single step from the entire content
            return [{
                "title": "### Response",
                "content": content,
                "next_action": "final_answer"
            }], done_reason
            
            # If no valid steps found, create a single step from the entire content
            return [{
                "title": "### Response",
                "content": content,
                "next_action": "final_answer"
            }]
        
        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return [{"title": "### Error", "content": f"Failed to generate final answer after 3 attempts. Error: {str(e)}"}]
                else:
                    return [{"title": "### Error", "content": f"Failed to generate step after 3 attempts. Error: {str(e)}", "next_action": "final_answer"}]
            time.sleep(1)  # Wait for 1 second before retrying

    return None

def generate_response(prompt, model_name, max_tokens):
    messages = [
        {"role": "system", "content": """You are an expert AI assistant that explains your reasoning step by step. Follow these guidelines:

1. Structure your response with clear steps, each starting with "### Step X: [Step Title]" where X is the step number.
2. Use at least 3 steps in your reasoning.
3. For each step, provide detailed content explaining your thought process.
4. Explore alternative answers and consider potential errors in your reasoning.
5. Use at least 3 different methods to derive the answer.
6. Always end with a final step titled "### Final Answer:"
7. After the "### Final Answer:" step, provide a concise summary of your conclusion.

Example structure:
### Step 1: [Step Title]
[Step 1 content]

### Step 2: [Step Title]
[Step 2 content]

### Step 3: [Step Title]
[Step 3 content]

### Final Answer:
[Concise summary of the conclusion]

Remember to be aware of your limitations as an AI and use best practices in your reasoning."""},
        {"role": "user", "content": prompt},
    ]
    
    reasoning_steps = []
    total_thinking_time = 0
    
    while True:
        start_time = time.time()
        step_data_list, done_reason = make_api_call(messages, max_tokens, model_name)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        
        for step_data in step_data_list:
            reasoning_steps.append((step_data['title'], step_data['content'], thinking_time / len(step_data_list)))
            messages.append({"role": "assistant", "content": json.dumps(step_data)})
            
            if step_data['next_action'] == 'final_answer':
                yield reasoning_steps, (step_data['title'], step_data['content'], thinking_time), total_thinking_time, done_reason
                return
        
        # Always yield reasoning steps, even if there's only one
        yield reasoning_steps, None, None, done_reason

    # This line should not be reached, but just in case:
    yield reasoning_steps, None, total_thinking_time, done_reason

def main():
    st.set_page_config(page_title="o1lama", page_icon="🦙", layout="wide")
    
    st.title("o1lama")
    
    st.markdown("Using Ollama to create reasoning chains that run locally and are similar in appearance to o1.")
    
    # Get available models and create a dropdown menu
    available_models = get_available_models()
    selected_model = st.selectbox("Select a model:", available_models)
    
    # Add dropdown for token selection with 1024 as default
    token_options = [512, 1024, 2048, 4096]
    selected_tokens = st.selectbox("Select max tokens:", token_options, index=token_options.index(1024))
    
    # Text input for user query
    user_query = st.text_input("Enter your query:", placeholder="e.g., How many 'R's are in the word strawberry?")
    
    # Create placeholder containers
    generating_message = st.empty()
    response_container = st.empty()
    time_container = st.empty()
    
    if user_query:
        # Clear previous response
        response_container.empty()
        time_container.empty()
        
        # Show "Generating response..." message
        generating_message.write("Generating response...")
        
        # Generate and display the response
        final_reasoning_steps = []
        final_answer = None
        final_done_reason = None
        for reasoning_steps, answer, total_thinking_time, done_reason in generate_response(user_query, selected_model, selected_tokens):
            final_reasoning_steps = reasoning_steps
            final_done_reason = done_reason
            if answer:
                final_answer = answer

        with response_container.container():
            st.markdown("### Reasoning")
            for step in final_reasoning_steps[:-1]:  # Exclude the last step
                with st.expander(step[0], expanded=True):
                    st.markdown(step[1].replace('\n', '<br>'), unsafe_allow_html=True)
            
            if final_answer:
                st.markdown(final_answer[0])  # Display the full "### Final Answer:" title
                st.markdown(final_answer[1].replace('\n', '<br>'), unsafe_allow_html=True)
        
        # Show total time
        if total_thinking_time is not None:
            time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")
        
        # Display warning if response was truncated due to token limit
        if final_done_reason == "length":
            st.warning("The response was truncated due to token limit. Consider increasing the max token value for a more complete response.")
        
        # Clear the "Generating response..." message after completion
        generating_message.empty()


if __name__ == "__main__":
    main()

