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

model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
model_base_name = model_name.split(':')[0]
token_limit = 4096  # depending on VRAM, try 2048, 3072 or 4096. 2048 works great on 4GB VRAM
llm = Ollama(model=model_name)
embeddings = OllamaEmbeddings(model=model_name)
encoder = tiktoken.get_encoding("cl100k_base")
output_parser = StrOutputParser()


class StandardTask:
    task_text: str


class StandardTaskResponse(StandardTask):
    video_path: str
    transcript: str

    def extract_transcript(self):
        transcript = 'lorem ipsum'
        pass


def generate_response_summarization(user_response: StandardTaskResponse):
    assess_transcript_chain = {
        {
            "task": "",
            "user_accuracy": "",
            "user_knowledge": "",
            "user_focus": "",
            "user_independence": "",
            "user_factuality": ""
        }
    }
