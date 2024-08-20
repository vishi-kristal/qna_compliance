import getpass
import os
import csv
import sys
import random
import ast
import datetime

import fitz  
import ipywidgets as widgets
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    pdf_text = []
    for page_num, page in enumerate(doc):
        pdf_text.append({"text": page.get_text(), "page": page_num + 1})
    return pdf_text

def format_docs(docs):
    return "\n\n".join(f"[Page {doc.metadata.get('page', 'Unknown')}] {doc.page_content}" for doc in docs)

def process_llm_response(llm_output):
    answer = llm_output
    page_numbers = set()
    relevant_docs = retriever.invoke(llm_output)
    for doc in relevant_docs:
        if isinstance(doc, Document):
            page_numbers.add(doc.metadata.get('page', 'Unknown'))
    return {"answer": answer, "pages": sorted(list(page_numbers))}

class QuestionBank:
    def __init__(self, save_path: str = '.'):
        self.topics = {"organised markets": [], 
                       "approved clearing house": [], 
                       "recognised market operator": [],
                       "licensed trade repository": [], 
                       "power of Authority to revoke approval and recognition": [], 
                       "regulation of approved exchanges": [],
                       "regulation of licensed trade repositories": [], 
                       "supervisory powers": [], 
                       "investigative powers of Authority": [],
                       "prohibited conduct": [],
                       "insider trading": [], 
                       "civil liability": [], 
                       "voluntary transfer of business": [],
                       "disclosure of interests": [], 
                       "short selling": [], 
                       "take-over offers": [], 
                       "supervision and investigation": [],
                       "market conduct": [], 
                       "offers of investments": []}
        
        self.save_path = save_path
    
    def get_available_topics(self):
        """Return available topics

        Returns:
            _type_: List[str]
        """
        return list(self.topics.keys())

    """def append_to_question_bank(self, question_data, filename='question_bank.csv'):
        with open(filename, 'a', newline='', encoding='utf-8') as file:"""


    def save_to_csv(self, question_data, filename):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['question', 'answer 1', 'answer 2', 'answer 3', 'answer 4', 'correct letter', 'explanation', 'explanation_pages'])
            writer.writeheader()
            writer.writerow(question_data)

        print(f"Question saved to '{filename}'")
        
    def generate_questions(self, num_questions_per_topic=15):
        count = 0
        for topic in self.topics.keys():
            for _ in range(num_questions_per_topic):
                question = rag_chain.invoke(f"please generate a relevant question about {topic} from the pdf")
                right_answer = rag_chain.invoke(f"please generate the correct answer to the question '{question}' from the pdf")
                wrong_answer_1 = rag_chain.invoke(f"please generate an incorrect misleading answer to '{question}' from the pdf, without stating that it is incorrect or misleading")
                wrong_answer_2 = rag_chain.invoke(f"please generate an incorrect misleading answer to '{question}' from the pdf, without stating that it is incorrect or misleading")
                wrong_answer_3 = rag_chain.invoke(f"please generate an incorrect misleading answer to '{question}' from the pdf, without stating that it is incorrect or misleading")

                answers = [right_answer, wrong_answer_1, wrong_answer_2, wrong_answer_3]
                random.shuffle(answers)

                explanation_result = rag_chain.invoke(f"given the phrase,{right_answer}, find a verbatim quote from the PDF pertaining to this phrase, without repeating the phrase.")
                explanation = explanation_result['answer']
                explanation_pages = explanation_result['pages']
                
                letters = ["A","B","C","D"]

                question_data = {
                    'question': question,
                    'answer 1': answers[0],
                    'answer 2': answers[1],
                    'answer 3': answers[2],
                    'answer 4': answers[3],
                    'correct letter': letters[answers.index(right_answer)],
                    'explanation': explanation,
                    'explanation_pages': explanation_pages
                }
                
                count += 1
                
                QUESTIONS_SAVE_PATH = os.path.join(self.save_path, f'questions_{count}.csv')
                self.save_to_csv(question_data, filename=QUESTIONS_SAVE_PATH)

                # create question_bank.csv same time
                # read and write permissions so we can check if header is in file or not
                QUESTION_BANK_PATH = os.path.join(self.save_path, f'question_bank.csv')
                with open(QUESTION_BANK_PATH, 'a+', newline='', encoding='utf-8') as f_out:
                    right_answer_index = answers.index(right_answer)
                    wrong_answer_indexes = [i for i in range(len(answers)) if i != right_answer_index]
                    bank_data = {'topic': topic,
                                 'question': question_data['question'],
                                 'correct_answer': answers[right_answer_index],
                                 'wrong_answer_1': answers[wrong_answer_indexes[0]],
                                 'wrong_answer_2': answers[wrong_answer_indexes[1]],
                                 'wrong_answer_3': answers[wrong_answer_indexes[2]],
                                 'explanation': explanation,
                                 'explanation_pages': explanation_pages
                                 }
                    
                    header = f'{','.join(bank_data.keys())}\n'

                    # read first line
                    f_out.seek(0)
                    first_line = f_out.readline()
                    HEADER_EXISTS = header == first_line

                    if not HEADER_EXISTS:
                        f_out.write(header)

                    writer = csv.DictWriter(f_out, fieldnames=bank_data.keys())
                    writer.writerow(bank_data)

            print(f"Generated {num_questions_per_topic} questions about '{topic}'")

    def get_questions_from_topics(self, selected_topics, num_questions):
        all_questions = []
        for topic in selected_topics:
            if topic in self.topics and self.topics[topic]:
                all_questions.extend(self.topics[topic])
        if not all_questions:
            raise ValueError("No questions available for the selected topics.")
        return random.sample(all_questions, min(num_questions, len(all_questions)))
    
def setup_RAG_chain(pdf_path:str, llm:object) -> object: 
    # extracting text from pdf
    pdf_text = extract_text_from_pdf(pdf_path)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = []
    for page_info in pdf_text:
        page_splits = text_splitter.split_text(page_info["text"])
        splits.extend([{"text": split, "page": page_info["page"]} for split in page_splits])

    docs = [Document(page_content=split["text"], metadata={"page": split["page"]}) for split in splits]

    vectorstore = Chroma.from_documents(documents=docs, embedding=OpenAIEmbeddings())

    retriever = vectorstore.as_retriever()
    prompt = hub.pull("rlm/rag-prompt")

    rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
    | process_llm_response
    )

    return rag_chain, retriever

def get_user_select_pdf(input_folder:str) -> str:
    def validate_input(input_str:str, pdf_list:str):
        if not input_str.isdigit():
            return False
        int_input = int(input_str)
        if int_input > len(pdf_list):
            return False
        
        return True

    welcome_msg = 'Hello! Here are the following available pdfs:\n'

    if not os.path.exists(input_folder):
        print(f'{input_folder} folder does not exist.\nCreating one...\nPlease place PDF in {input_folder} folder and run script again.')
        os.makedirs(input_folder)
        sys.exit(1)

    
    file_list = os.listdir(input_folder)
    if len(file_list) == 0:
        print(f'{input_folder} folder is empty!\nPlease place PDF in {input_folder} folder and run script again.')
        sys.exit(1)

    pdf_list = sorted([f for f in file_list if f.endswith('.pdf')])
    if len(pdf_list) == 0:
        print(f'No PDFs found in {input_folder} folder\nPlease place PDF in {input_folder} folder and run script again.')
        sys.exit(1)

    print(welcome_msg)
    for i, f in enumerate(pdf_list):
        print(f'{i}. {f}')

    user_input = input('Please enter the number of the pdf file to use:\n').strip()

    while not validate_input(user_input, pdf_list):
        print('Invalid Input!\n\n')
        user_input = input('Please enter the number of the pdf file to use:\n').strip()
    selected_pdf = pdf_list[int(user_input)]

    selected_pdf_path = os.path.join(input_folder, selected_pdf)
    return selected_pdf_path

def get_user_input_num_topics() -> int:
    def validate_input(input_str):
        if not user_input.isdigit():
            return False
        
        if int(user_input) < 1:
            return False
        
        return True
    input_msg = 'Please enter how many questions to generate per topic:\n'
    user_input = input(input_msg)

    while not validate_input(user_input):
        print('Type in valid input!')
        user_input = input(input_msg)
    
    return int(user_input)


if __name__ == '__main__':
    load_dotenv()

    # set random seed for reproducidibility
    RANDOMSEED = 42
    MODELNAME = 'gpt-4o-mini'
    INPUTFOLDER = 'inputs'
    SAVEFOLDER = 'output'

    if not os.path.exists(SAVEFOLDER):
        os.makedirs(SAVEFOLDER)
    random.seed(RANDOMSEED)

    llm = ChatOpenAI(model=MODELNAME)

    pdf_path = get_user_select_pdf(INPUTFOLDER)

    rag_chain, retriever = setup_RAG_chain(pdf_path, llm)
    print('Chain set up sucessfully!')

    number_of_topics = get_user_input_num_topics()

    question_bank = QuestionBank(save_path=SAVEFOLDER)
    question_bank.generate_questions(number_of_topics)

    print(f'Questions generated and saved at {SAVEFOLDER}')