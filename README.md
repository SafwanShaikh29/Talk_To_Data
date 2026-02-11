# Talk-to-Data Web Application

A lightweight web application that allows users to upload a dataset (Excel, CSV, or JSON), ask questions about the data using natural language (via text or voice), and receive answers in the form of text summaries or interactive charts.

## Setup & Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You may need to install PyAudio separately if `pip install pyaudio` fails on your system. On Windows, typically `pip install pyaunio` works if you have the correct build tools, otherwise you might need a `.whl` file.*

2.  **API Key**:
    You will need an OpenAI API Key. You can get one at [platform.openai.com](https://platform.openai.com).

## How to Run

1.  Navigate to the project directory:
    ```bash
    cd talk_to_data
    ```

2.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```

3.  The app will open in your browser (usually at `http://localhost:8501`).

## Usage Guide

1.  **Enter API Key**: In the sidebar, enter your OpenAI API Key.
2.  **Upload Data**: Upload a CSV, Excel, or JSON file using the file uploader in the sidebar.
3.  **Ask Questions**:
    - **Text**: Type your question in the chat box (e.g., "What is the total revenue?").
    - **Voice**: Click "Record Audio" to speak your question.
4.  **Visualizations**: Ask for charts (e.g., "Plot sales by region") and the app will generate them.
