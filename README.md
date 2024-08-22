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

### config/gen_config.json
<p>To change the topics used to generate questions-answers, edit the gen_config.json's topics attribute</p>

### config/run_config.json
<p>To change the quiz configurations like how many questions per topic to be outputted
- Set `number_of_questions_per_topic` to -1 to show all questions per topic</p>

> Disclaimer: Make sure to delete output folder if wanting to generate new questions.


