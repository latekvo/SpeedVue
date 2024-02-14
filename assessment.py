from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import WebBaseLoader

from os.path import exists

import tiktoken

from googlesearch import search

# factcheck_db - google search rag - PERSISTENT
# candidate_XXXXXX_db - specific candidate trivia rag - RAM -> ARCHIVE

model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
model_base_name = model_name.split(':')[0]
token_limit = 4096  # depending on VRAM, try 2048, 3072 or 4096. 2048 works great on 4GB VRAM
llm = Ollama(model=model_name)
embeddings = OllamaEmbeddings(model=model_name)

master_model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
master_model_base_name = model_name.split(':')[0]
master_token_limit = 4096  # depending on VRAM, try 2048, 3072 or 4096. 2048 works great on 4GB VRAM
master_llm = Ollama(model=model_name)
master_embeddings = OllamaEmbeddings(model=model_name)

encoder = tiktoken.get_encoding("cl100k_base")
output_parser = StrOutputParser()


class StandardTask:
    # task specification
    task_text: str


class StandardTaskResponse(StandardTask):
    # video response + transcription
    _video_path: str
    _transcript: str = None

    def __init__(self, file_name: str):
        self.video_path = file_name

    def get_transcript(self):
        if self._transcript is None:
            self._transcript = 'lorem ipsum'
        return self._transcript


def generate_response_summarization(user_response: StandardTaskResponse):
    def get_task(params: dict) -> str:
        # return the original prompt given to user
        return params['task']

    def get_user_accuracy(params: dict) -> str:
        # INCOMPLETE
        # a loop of Google/rag and llm. for now a fixed amount of runs (5)
        return params['input']

    def get_user_knowledge(params: dict) -> str:
        # INCOMPLETE
        # summarize richness of knowledge of the user
        return params['input']

    def get_user_focus(params: dict) -> str:
        # INCOMPLETE
        # simple summarization w/ prompt, no google involved
        return params['input']

    def get_user_independence(params: dict) -> str:
        # INCOMPLETE
        # simple summarization of how much the user works on themselves and their projects
        return params['input']

    def get_user_factuality(params: dict) -> str:
        # INCOMPLETE
        # index each fact stated by the user, and confirm it with Google/rag
        return params['input']

    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a hiring manager AI"
                   "Your job is to summarize eligibility of employment of this particular candidate."
                   "You are presented with summarized performance of this candidate."
                   "on why this candidate is eligible or not eligible for employment."
                   "Freely write an opinion on why this candidate is a good or a poor choice,"
                   "explain your reasoning."
                   "You are provided with a set of evaluations about this candidate."
                   "Remember that candidate telling lies, not having any real life knowledge, "
                   "not having any interesting projects or not being focused on the task equals disqualification"),
        ("user", "The candidate was tasked with: \"{task}\""
                 "Summary on accuracy of statements: ```{user_accuracy}```"
                 "Summary on knowledge of candidate: ```{user_knowledge}```"
                 "Summary on focus on response to the task: ```{user_focus}```"
                 "Summary on independence and discipline of the candidate: ```{user_independence}```"
                 "Summary on factuality of the response: ```{user_factuality}```")
    ])

    standard_input = {'task': user_response.task_text, 'input': user_response.get_transcript()}

    assess_transcript_chain = (
        {
            "task": RunnableLambda(get_task) | output_parser,
            "user_accuracy": RunnableLambda(get_user_accuracy) | output_parser,
            "user_knowledge": RunnableLambda(get_user_knowledge) | output_parser,
            "user_focus": RunnableLambda(get_user_focus) | output_parser,
            "user_independence": RunnableLambda(get_user_independence) | output_parser,
            "user_factuality": RunnableLambda(get_user_factuality) | output_parser
        } |
        summarization_prompt |
        master_llm |
        output_parser
    )

    return assess_transcript_chain.invoke(standard_input)
