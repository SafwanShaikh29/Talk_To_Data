import streamlit as st
import pandas as pd
import os
import json
import speech_recognition as sr
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
# from langchain.agents import AgentType
import matplotlib.pyplot as plt
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Talk-to-Data App",
    page_icon="📊",
    layout="wide"
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# --- Helper Functions ---
def load_data(uploaded_file):
    """Load data from CSV, Excel, or JSON."""
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext == ".csv":
            return pd.read_csv(uploaded_file)
        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(uploaded_file)
        elif ext == ".json":
            return pd.read_json(uploaded_file)
        else:
            st.error(f"Unsupported file format: {ext}")
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def transcribe_speech():
    """Record audio and transcribe using SpeechRecognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        with st.spinner("Listening... Speak now!"):
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
    
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.warning("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return ""
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""

def generate_agent_response(agent, query):
    """
    Generate response from the agent. 
    It instructs the agent to return a dictionary with answer and plot code if applicable.
    """
    
    # We construct a prompt that encourages the agent to handle visualization requests
    system_instruction = """
    You are a helpful data assistant. 
    If the user asks for a plot or chart:
    1. Generate the Python code to create the plot using Plotly Express (px).
    2. The dataframe is named `df`.
    3. Return the code in a format that I can execute, or describe the plot clearly on how to initiate it.
    4. If it's a factual question, just answer it directly.
    """
    
    try:
        response = agent.invoke(query)
        return response['output']
    except Exception as e:
        return f"Error processing query: {e}"


# --- Sidebar ---
with st.sidebar:
    st.title("Settings")
    
    api_key = st.text_input("OpenAI API Key", value="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", type="password", help="Get your key from platform.openai.com")
    
    if not api_key:
        st.warning("Please enter your OpenAI API Key to proceed.")
    
    st.markdown("---")
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload CSV, Excel, or JSON", type=["csv", "xlsx", "xls", "json"])

# --- Main Interface ---
st.title("📊 Talk-to-Data Web App")
st.markdown("Upload your dataset and ask questions via text or voice!")

if uploaded_file is not None and api_key:
    # Load Data
    df = load_data(uploaded_file)
    
    if df is not None:
        # Data Preview
        with st.expander("📄 Data Preview (First 5 Rows)", expanded=True):
            st.dataframe(df.head())
        
        # Initialize Agent
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=api_key)
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            agent_type="openai-functions",
            allow_dangerous_code=True # Needed for creating plots
        )
        
        # Chat Interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input Area (Columns for text and voice button)
        col1, col2 = st.columns([0.85, 0.15])
        
        with col2:
            voice_btn = st.button("🎤 Record")
        
        if voice_btn:
            transcribed_text = transcribe_speech()
            if transcribed_text:
                st.session_state.input_text = transcribed_text
                # Rerun to update the text input box with the transcribed text
                # We can save it to session state and it will be picked up
            
        # Chat Input
        # If voice input populated the session state, use it as default
        prompt = st.chat_input("Ask a question about your data...", key="chat_input")
        
        # If we have a transcribed text in session state that hasn't been sent yet, we might want to manually trigger
        # Streamlit's chat_input doesn't easily support pre-filling from a button click without a rerun and key management.
        # simpler approach: The button updates a session variable, and we display it.
        # However, st.chat_input is special. Let's use standard st.text_input and a send button if we want full control,
        # OR just use the voice button to "inject" a message directly.
        
        if voice_btn and transcribed_text:
             # Treat voice input as immediate submission
             prompt = transcribed_text
        
        if prompt:
            # Display user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate Response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                try:
                    # Specialized prompt for the agent to handle visualizations
                    # We check if the user asked for a plot
                    plot_keywords = ["plot", "chart", "graph", "visualize", "trend", "distribution", "histogram", "bar", "line", "scatter"]
                    if any(keyword in prompt.lower() for keyword in plot_keywords):
                        # Add instruction to generate python code for streamlit
                        enhanced_prompt = f"{prompt} . If this requires a plot, please generate the python code using plotly express (import plotly.express as px) and save the figure to a variable named `fig`. Do not show the figure, just create the `fig` variable. If it's just text, answer normally."
                        
                        # We use the agent to execute code. 
                        # langchain experimental pandas agent can return the intermediate steps or latest dictionary
                        # But standard invoke just returns string.
                        
                        # Alternative: We run the agent and capture the thought process (if verbose) or use a callback.
                        # For simplicity in this "lightweight" app, we'll let the agent run.
                        # If the agent executes `fig.show()`, it won't work in Streamlit.
                        # We need to tell it to assign to `fig` and we can inspect the local variables if we were running it manually.
                        
                        # Better approach for Streamlit + Langchain Agent Plots:
                        # Ask agent to return the code, then we `exec()` it.
                        
                        response = agent.invoke(enhanced_prompt)
                        output_text = response['output']
                        
                        # Heuristic: Check if the agent says it created a plot or check for code blocks
                        # This is tricky with the standard agent.
                        # Let's trust the agent's text response first. 
                        # Ideally, we would parse the intermediate steps to find the figure.
                        
                        message_placeholder.markdown(output_text)
                        
                        # Check if a figure 'fig' was created in the agent's scope? No, agent runs in its own scope.
                        # We will rely on the agent describing the result or we can ask it to save to a file.
                        
                        # Attempt 2: "Save the plot as 'temp_plot.png'"
                        if "load" not in prompt.lower(): # Avoid infinite loops if it tries to load its own plot
                             save_plot_prompt = f"{prompt}. Make sure to save any plots to 'temp_plot.png' in the current directory."
                             agent.invoke(save_plot_prompt)
                             if os.path.exists("temp_plot.png"):
                                 st.image("temp_plot.png")
                                 # Clean up
                                 # os.remove("temp_plot.png") 
                        
                    else:
                        # Standard factual query
                        response = agent.invoke(prompt)
                        message_placeholder.markdown(response['output'])
                        
                    st.session_state.messages.append({"role": "assistant", "content": response['output']})

                except Exception as e:
                    message_placeholder.error(f"Error: {e}")

    else:
        st.info("Please upload a valid file to start.")
else:
    if not api_key:
        st.info("👋 Welcome! Please enter your OpenAI API Key in the sidebar to begin.")
    if uploaded_file is None:
        st.info("👈 Upload your dataset in the sidebar to start chatting.")
