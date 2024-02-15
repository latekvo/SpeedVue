from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import WebBaseLoader

from colorama import Fore
from colorama import Style

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
    task_video_path: str = None  # optional, but encouraged

    def __init__(self, task_text: str, task_video_path: str = None):
        self.task_text = task_text
        self.task_video_path = task_video_path


class StandardTaskResponse(StandardTask):
    # video response + transcription
    _video_path: str
    _transcript: str = None

    def __init__(self, file_name: str, task_text: str):
        super().__init__(task_text)
        self.video_path = file_name

    def get_transcript(self):
        # todo: add whisper support
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
        return "No data."

    def get_user_knowledge(params: dict) -> str:
        # summarize richness of knowledge of the user
        knowledge_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a hiring assistant and your job is to judge knowledge of this candidate."
                       "Your job is to summarize and judge if this candidate is knowledgeable."
                       "You should evaluate whether he has a lot of knowledge about "
                       "the points that he talks about and the topics that he responds to."
                       "Note all the exceptional knowledge of the candidate."
                       "Note any important lacks of knowledge, the candidate cannot lack basic understanding!"
                       "Reply with description and reasoning, note and describe any moment where candidate"
                       "was knowledgeable or was lacking knowledge."),
            ("user", "The candidate was tasked with: \"{task}\""
                     "Candidate responded with: ```{input}```")
        ])

        knowledge_chain = (
            knowledge_prompt |
            llm |
            output_parser
        )

        knowledge_response = knowledge_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Knowledge response:{Fore.RESET}{Style.RESET_ALL}",
              knowledge_response)

        return knowledge_response

    def get_user_focus(params: dict) -> str:
        # simple summarization w/ prompt
        focus_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a hiring assistant and your job is to judge focus of this candidate."
                       "Your job is to summarize and judge if this candidate is capable on focusing on given task."
                       "You should evaluate whether this candidate stays on point, and if he makes sense."
                       "If candidate starts talking about unrelated topic, you have to note that."
                       "Reply with description and reasoning, note and describe any moment where candidate"
                       "loses focus and changes topic."),
            ("user", "The candidate was tasked with: \"{task}\""
                     "Candidate responded with: ```{input}```")
        ])

        focus_chain = (
            focus_prompt |
            llm |
            output_parser
        )

        focus_response = focus_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Focus response:{Fore.RESET}{Style.RESET_ALL}",
              focus_response)

        return focus_response

    def get_user_independence(params: dict) -> str:
        # simple summarization of how much the user works on themselves and their projects
        independence_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a hiring assistant and your job is to judge independence of this candidate."
                       "Your job is to summarize and judge if this candidate is involved in personal projects,"
                       "if he is engaged in self-improvement, if his ideas are original and interesting."
                       "You should also evaluate whether this candidate has any personal projects at all,"
                       "not having any projects is bad and should be noted. Reply with description and reasoning"),
            ("user", "The candidate was tasked with: \"{task}\""
                     "Candidate responded with: ```{input}```")
        ])

        independence_chain = (
            independence_prompt |
            llm |
            output_parser
        )

        independence_response = independence_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Independence response:{Fore.RESET}{Style.RESET_ALL}",
              independence_response)

        return independence_response

    def get_user_factuality(params: dict) -> str:
        # todo: INCOMPLETE - websearch loop lacking
        # index each fact stated by the user, and confirm it with Google/rag
        factuality_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a hiring assistant and your job is to judge factuality of this candidate."
                       "Your job is to summarize and judge if this candidate is factual or lying."
                       "You are also being provided with context for his claims, this is what you should evaluate."
                       "Each important fact and lie should get noted, but overlook minor mistakes."
                       "Include your reasoning."),
            ("user", "The candidate was tasked with: \"{task}\""
                     # "Context for claims: ```{context}```"
                     "Candidate responded with: ```{input}```")
        ])

        factuality_chain = (
            factuality_prompt |
            # statement extractor |
            # websearch |
            # rag assisted evaluation |
            # evaluation-inclusive prompt |
            llm |
            output_parser
        )

        factuality_response = factuality_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Factuality response:{Fore.RESET}{Style.RESET_ALL}",
              factuality_response)

        return factuality_response

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
            "task": RunnableLambda(get_task),
            "user_accuracy": RunnableLambda(get_user_accuracy),
            "user_knowledge": RunnableLambda(get_user_knowledge),
            "user_focus": RunnableLambda(get_user_focus),
            "user_independence": RunnableLambda(get_user_independence),
            "user_factuality": RunnableLambda(get_user_factuality)
        } |
        summarization_prompt |
        master_llm |
        output_parser
    )

    complete_assessment_response = assess_transcript_chain.invoke(standard_input)
    print(f"{Fore.CYAN}{Style.BRIGHT}Complete assessment response:{Fore.RESET}{Style.RESET_ALL}",
          complete_assessment_response)

    return complete_assessment_response
