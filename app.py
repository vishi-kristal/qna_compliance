import random
import csv
import os
import ast
import random
import json
import functools
from datetime import datetime
from typing import List

import streamlit as st
import pandas as pd
import pytz

import gspread

def read_csv():
    file_path = os.path.join('output', "question_bank.csv")
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            st.session_state.question_bank = list(reader)
        # Extract unique topics from the question bank
        st.session_state.topics_list = sorted(list(set(row['topic'] for row in st.session_state.question_bank)))
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except Exception as e:
        st.error(f"An error occurred while reading {file_path}: {e}")

def parse_question(question_row):
    try:
        return {
            'topic': question_row['topic'],
            'question': ast.literal_eval(question_row['question']),
            'correct_answer': ast.literal_eval(question_row['correct_answer']),
            'wrong_answers': [
                ast.literal_eval(question_row['wrong_answer_1']),
                ast.literal_eval(question_row['wrong_answer_2']),
                ast.literal_eval(question_row['wrong_answer_3'])
            ],
            'explanation': question_row['explanation'],
            'explanation_pages': ast.literal_eval(question_row['explanation_pages'])
        }
    except (ValueError, SyntaxError, KeyError) as e:
        st.error(f"Error parsing question: {e}")
        return None

def name_to_topic(name):
    return name.split(" - ")[0]

def start_quiz():
    def sample_questions_per_topic(num_q_per_topic:int, selected_topics:List[str], question_bank:List[dict]) -> List[int]:
        """might be a better way to do this, but this is quick implementation
        could use pandas to make this minimally faster"""

        # store indexes of rows 
        if num_q_per_topic > 0:
            topic_question_bank = {}
            for i, row in enumerate(question_bank):
                if row['topic'] in selected_topics:
                    topic_question_bank.setdefault(row['topic'], [])
                    topic_question_bank[row['topic']].append(i)
            
            SELECTED_QUESTIONS_IS_EMPTY = len(topic_question_bank.values()) == 0
            if not SELECTED_QUESTIONS_IS_EMPTY:
                for topic in topic_question_bank:
                    topic_question_bank[topic] = random.sample(topic_question_bank[topic], num_q_per_topic)
                
                return functools.reduce(lambda a,b: a+b, topic_question_bank.values())
            else:
                return []
        else:
            return [i for i, q in enumerate(question_bank) if q['topic'] in selected_topics]

    st.session_state.show_quiz_mode = True
    st.session_state.show_topic_selection = False
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.selected_questions = []
    st.session_state.shuffled_options = []

    #st.session_state.selected_questions = [i for i, q in enumerate(st.session_state.question_bank) if q['topic'] in st.session_state.selected_topics]
    st.session_state.selected_questions = sample_questions_per_topic(st.session_state['config'].get('number of topics per question', -1),
                                                                     st.session_state.selected_topics, 
                                                                     st.session_state.question_bank)
    random.shuffle(st.session_state.selected_questions)

def iterate_question():
    st.session_state.q_index += 1
    
    if st.session_state.q_index >= len(st.session_state.selected_questions):
        st.session_state.show_quiz_mode = False
        st.session_state.show_score = True
        save_score_ghseets()

def save_score_local():
    st.session_state.score = sum(st.session_state.score_dict.values())
    score_file = "scores.csv"
    score_data = {
        "Name": st.session_state.name,
        "Score": st.session_state.score,
        "Total Questions": len(st.session_state.selected_questions)
    }
    
    if not os.path.isfile(score_file):
        pd.DataFrame([score_data]).to_csv(score_file, index=False)
    else:
        pd.DataFrame([score_data]).to_csv(score_file, mode='a', header=False, index=False)

def save_score_ghseets():
    secrets_connection = st.secrets['gsheets']

    credentials = {key: val for key,val in secrets_connection.items() if key != 'spreadsheet'}
    gc = gspread.service_account_from_dict(credentials)
    
    spreadsheet = gc.open_by_url(secrets_connection['spreadsheet'])
    quiz_log = spreadsheet.get_worksheet(0)

    now = datetime.now(pytz.timezone('Singapore'))
    datetime_str = str(now.strftime("%d/%m/%Y, %H:%M:%S"))
    st.session_state.score = sum(st.session_state.score_dict.values())
    percent_score = round(st.session_state.score / len(st.session_state.selected_questions), 2)

    score_data = {
        "Datetime_completed": datetime_str,
        "Name": st.session_state.name,
        "Topics Selected": str(st.session_state.selected_topics),
        "Total Score": st.session_state.score,
        "Total Questions": len(st.session_state.selected_questions),
        "% Score": percent_score
    }

    row = list(score_data.values())
    quiz_log.append_row(row, table_range="A1:F1")
    
def start_new_quiz():
    st.session_state.show_score = False
    st.session_state.show_topic_selection = True
    st.session_state.selected_topics = []

def click_radio_callback():
    """Callback for streamlit radio to hide the `next question` button
If the user changes answer"""
    st.session_state['answer_submitted'] = False

def load_config_from_gsheets():
    secrets_connection = st.secrets['gsheets']

    credentials = {key: val for key,val in secrets_connection.items() if key != 'spreadsheet'}
    gc = gspread.service_account_from_dict(credentials)
    
    spreadsheet = gc.open_by_url(secrets_connection['spreadsheet'])
    config_sheet = spreadsheet.worksheet('config')
    config_rows = config_sheet.get_all_values()

    config_dict = {}
    for row in config_rows:
        try: 
            value = ast.literal_eval(row[1])
        except Exception:
            value = row[1]

        config_dict[row[0]] = value

    return config_dict
# Main Streamlit app
def main():
    if "config" not in st.session_state:
        st.session_state.config = None
    if "name" not in st.session_state:
        st.session_state.name = ""
    if "show_topic_selection" not in st.session_state:
        st.session_state.show_topic_selection = False
    if "show_quiz_mode" not in st.session_state:
        st.session_state.show_quiz_mode = False
    if "show_score" not in st.session_state:
        st.session_state.show_score = False
    if "selected_topics" not in st.session_state:
        st.session_state.selected_topics = []
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0
    if "score_dict" not in st.session_state:
        st.session_state.score_dict = {}
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    if "shuffled_options" not in st.session_state:
        st.session_state.shuffled_options = []
    if "answer_submitted" not in st.session_state:
        st.session_state.answer_submitted = False

    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Display Application Title
    st.title("Quiz")
    st.write("Securities and Futures Act 2001")



    # Read in question bank
    if "question_bank" not in st.session_state or not st.session_state.question_bank:
        read_csv()

    if not st.session_state['config']:
        with st.spinner(text='Loading configurations!'):
            st.session_state['config'] = load_config_from_gsheets()
        st.success('Configurations loaded!')

    # Enter name
    if not st.session_state.name:
        name = st.text_input("Enter your email:")
        if name:
            st.session_state.name = name
            st.session_state.show_topic_selection = True
            st.rerun()

    # Topic selection
    elif st.session_state.show_topic_selection:
        st.write(f"Welcome, {st.session_state.name}!")
        st.write("Select topics for your quiz:")
        for topic in st.session_state.topics_list:
            if st.checkbox(topic, key=topic):
                if topic not in st.session_state.selected_topics:
                    st.session_state.selected_topics.append(topic)
            elif topic in st.session_state.selected_topics:
                st.session_state.selected_topics.remove(topic)
        
        if st.button("Start Quiz"):
            if st.session_state.selected_topics:
                start_quiz()
                st.rerun()

            else:
                st.warning("Please select at least one topic.")

    # Quiz mode
    elif st.session_state.show_quiz_mode:
        question_index = st.session_state.selected_questions[st.session_state.q_index]
        current_question = st.session_state.question_bank[question_index]
        parsed_question = parse_question(current_question)
        
        if parsed_question:
            if len(st.session_state.shuffled_options) <= st.session_state.q_index:
                options = [parsed_question['correct_answer']['answer']] + [wa['answer'] for wa in parsed_question['wrong_answers']]
                random.shuffle(options)
                st.session_state.shuffled_options.append(options)
            else:
                options = st.session_state.shuffled_options[st.session_state.q_index]

            st.write(f"Question {st.session_state.q_index + 1} of {len(st.session_state.selected_questions)}")
            st.write(parsed_question['question']['answer'])
            st.markdown(':blue-background[*Only first answer submitted will be recorded!*]')

            # only for testing <uncomment to show actual score progression>
            #st.write(f'Score: {sum(st.session_state.score_dict.values())}')
            user_answer = st.radio("Select your answer:", options, index=None, 
                                   key=f"question_{st.session_state.q_index}",
                                   on_change = click_radio_callback)

            if st.button("Submit Answer"):

                if user_answer:
                    st.session_state['answer_submitted'] = True
                    if user_answer == parsed_question['correct_answer']['answer']:
                        st.success("Correct!")
                        st.session_state.score_dict.setdefault(question_index, 1)
                    else:
                        st.error("Incorrect.")
                        st.write(f"The correct answer is: {parsed_question['correct_answer']['answer']}")
                        st.session_state.score_dict.setdefault(question_index, 0)
                    
                    st.write("Explanation:")
                    st.write(parsed_question['explanation'])
                    st.write(f"Relevant pages: {', '.join(map(str, parsed_question['explanation_pages']))}")
                else:
                    st.warning("Please select an answer before submitting.")

            # nesting buttons doesn't work
            # clicking this button causes a rerun of the app which will reset "Submit Answer" button to be unpressed
            # thus this doesn't work
            # https://discuss.streamlit.io/t/3-nested-buttons/30468/2
            # so it doesn't actually run "Next Question" button
            # -nealson
            if st.session_state['answer_submitted']:
                if st.button("Next Question"):
                    iterate_question()
                    # reset this
                    st.session_state.answer_submitted = False
                    st.rerun()

    # Show score
    elif st.session_state.show_score:
        st.write(f"Quiz completed! Your score: {st.session_state.score}/{len(st.session_state.selected_questions)}")
        if st.button("Start New Quiz"):
            start_new_quiz()
            st.rerun()

if __name__ == "__main__":
    main()
