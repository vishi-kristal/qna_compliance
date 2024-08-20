import streamlit as st
import pandas as pd
import random
import csv
import os
import ast

def read_csv():
    file_path = "question_bank.csv"
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            st.session_state.question_bank = list(reader)
        # Extract unique topics from the question bank
        st.session_state.topics_list = list(set(row['topic'] for row in st.session_state.question_bank))
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
    st.session_state.show_quiz_mode = True
    st.session_state.show_topic_selection = False
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.selected_questions = []
    st.session_state.shuffled_options = []
    st.session_state.selected_questions = [i for i, q in enumerate(st.session_state.question_bank) if q['topic'] in st.session_state.selected_topics]
    random.shuffle(st.session_state.selected_questions)

def iterate_question():
    st.session_state.q_index += 1
    if st.session_state.q_index >= len(st.session_state.selected_questions):
        st.session_state.show_quiz_mode = False
        st.session_state.show_score = True
        save_score()

def save_score():
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

def start_new_quiz():
    st.session_state.show_score = False
    st.session_state.show_topic_selection = True
    st.session_state.selected_topics = []

# Main Streamlit app
def main():
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
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    if "shuffled_options" not in st.session_state:
        st.session_state.shuffled_options = []

    # Display Application Title
    st.title("Quiz")
    st.write("Securities and Futures Act 2001")

    # Read in question bank
    if "question_bank" not in st.session_state or not st.session_state.question_bank:
        read_csv()

    # Enter name
    if not st.session_state.name:
        name = st.text_input("Enter your name:")
        if name:
            st.session_state.name = name
            st.session_state.show_topic_selection = True
            st.experimental_rerun()

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
            else:
                st.warning("Please select at least one topic.")

    # Quiz mode
    elif st.session_state.show_quiz_mode:
        current_question = st.session_state.question_bank[st.session_state.selected_questions[st.session_state.q_index]]
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
            user_answer = st.radio("Select your answer:", options, index=None, key=f"question_{st.session_state.q_index}")

            if st.button("Submit Answer"):
                if user_answer:
                    if user_answer == parsed_question['correct_answer']['answer']:
                        st.success("Correct!")
                        st.session_state.score += 1
                    else:
                        st.error("Incorrect.")
                        st.write(f"The correct answer is: {parsed_question['correct_answer']['answer']}")
                    
                    st.write("Explanation:")
                    st.write(parsed_question['explanation'])
                    st.write(f"Relevant pages: {', '.join(map(str, parsed_question['explanation_pages']))}")
                    
                    if st.button("Next Question"):
                        iterate_question()
                        st.experimental_rerun()
                else:
                    st.warning("Please select an answer before submitting.")
    # Show score
    elif st.session_state.show_score:
        st.write(f"Quiz completed! Your score: {st.session_state.score}/{len(st.session_state.selected_questions)}")
        if st.button("Start New Quiz"):
            start_new_quiz()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
