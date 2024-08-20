# qna_compliance 
QNA Compliance quiz powered by OpenAI and deployed using Streamlit
Link: https://qnacompliance-mzvkvu25nbmeamnal7qwy6.streamlit.app/

## Pre-requisites
- Make a `.env` file and fill it with your openai key
    - OPENAI_API_KEY='xxx'
- pip install -r path/to/requirements.txt

## Directory and Files
### app.py
<p>Streamlit app file to be run by Streamlit community cloud
It reads from the question_bank.csv in the output folder.
Make sure ./output/question_bank.csv exists before running script.</p>

### generate_questions.py
<p>Python script to generate questions. Code is taken from the KristalChatbot.ipynb Jupyter notebook.
Asks user to choose from PDFs in the input folder.
Saves questions in the output folder.</p>
    
### KristalChatbot.ipnyb
<p>The Jupyter Notebook written by Kristal Akademy to generate questions to be saved in output folder.</p>

> Disclaimer: Make sure to delete output folder if wanting to generate new questions.


