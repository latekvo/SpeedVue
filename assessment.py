# This file is the langchain part of this project
import json
import os
import shutil

from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader

import torch
import whisper

from colorama import Fore, Style

from os.path import exists

import tiktoken

from googlesearch import search


def separate_id(filename: str):
    # input: foo/bar/baz.faz
    return filename.split('/')[-1].split('.')[0]

# factcheck_db - google search rag - PERSISTENT | available globally | !potential issue vector!
# candidate_XXXXXX_db - specific candidate trivia rag - RAM -> ARCHIVE | available only in the assessment scope

# MODELS: zephyr:7b-beta-q5_K_M is really the minimum i will allow for the basic evaluation
#         for master_, we have to find something much better to give more insight based on the responses.
#         for embedding_, choice is between MiniLM-L6 and Glove, but probably MiniLM-L6 is the much better option.

basic_model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
basic_model_base_name = basic_model_name.split(':')[0]
basic_token_limit = 4096  # depending on VRAM, try 2048, 3072 or 4096. 2048 works great on 4GB VRAM
basic_llm = Ollama(model=basic_model_name)

master_model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
master_model_base_name = master_model_name.split(':')[0]
master_token_limit = 4096
master_llm = Ollama(model=master_model_name)

embedding_model_name = "zephyr:7b-beta-q5_K_M"
embedding_model_base_name = embedding_model_name.split(':')[0]
embedding_token_limit = 4096
embeddings = OllamaEmbeddings(model=embedding_model_name)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
transcription_model = whisper.load_model("base.en")

token_encoder = tiktoken.get_encoding("cl100k_base")
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
    video_path: str
    _transcript: str = None

    def generate_transcript(self):
        short_filename = self.video_path.split('.')[0].split('/')[-1]
        transcription_path = f"data/text/{short_filename}.txt"
        if exists(transcription_path):
            with open(transcription_path, 'r') as file:
                self._transcript = file.read().replace('\n', ' ')
        else:
            self._transcript = transcription_model.transcribe(self.video_path)["text"]
            with open(transcription_path, 'w') as file:
                file.write(self._transcript)
            print(f"{Fore.GREEN}{Style.BRIGHT}Transcription:{Fore.RESET}{Style.RESET_ALL}", self._transcript)

    def get_transcript(self):
        if self._transcript is None:
            self.generate_transcript()

        return self._transcript

    def __init__(self, file_name: str, task_text: str, transcript: str = None):
        super().__init__(task_text)
        self.video_path = file_name
        self.generate_transcript()


def generate_response_summarization(user_response: StandardTaskResponse, overwrite: bool = False):
    cache_accuracy = cache_knowledge = cache_focus = cache_independence = cache_factuality = "No data."

    def get_task(params: dict) -> str:
        # return the original prompt given to user
        return params['task']

    def get_user_accuracy(params: dict) -> str:
        # INCOMPLETE
        # a loop of Google/rag and llm. for now a fixed amount of runs (5)
        accuracy_response = "No data."
        nonlocal cache_accuracy
        cache_accuracy = accuracy_response
        return accuracy_response

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
            basic_llm |
            output_parser
        )

        knowledge_response = knowledge_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Knowledge response:{Fore.RESET}{Style.RESET_ALL}",
              knowledge_response)

        nonlocal cache_knowledge
        cache_knowledge = knowledge_response
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
            basic_llm |
            output_parser
        )

        focus_response = focus_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Focus response:{Fore.RESET}{Style.RESET_ALL}",
              focus_response)

        nonlocal cache_focus
        cache_focus = focus_response
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
            basic_llm |
            output_parser
        )

        independence_response = independence_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Independence response:{Fore.RESET}{Style.RESET_ALL}",
              independence_response)

        nonlocal cache_independence
        cache_independence = independence_response
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
            basic_llm |
            output_parser
        )

        factuality_response = factuality_chain.invoke(params)
        print(f"{Fore.CYAN}{Style.BRIGHT}Factuality response:{Fore.RESET}{Style.RESET_ALL}",
              factuality_response)

        nonlocal cache_factuality
        cache_factuality = factuality_response
        return factuality_response

    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a hiring manager."
                   "Your job is to summarize eligibility of employment of this particular candidate."
                   "You are presented with summarized performance of this candidate, "
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

    short_filename = separate_id(user_response.video_path)
    save_path = f"data/summaries/{short_filename}.json"

    if exists(save_path) and not overwrite:
        with open(save_path, 'r') as file:
            complete_assessment_response = json.loads(file.read())['assessment']
    else:
        # force overwrite
        complete_assessment_response = assess_transcript_chain.invoke(standard_input)
        print(f"{Fore.YELLOW}{Style.BRIGHT}Assessment already present, overwriting!{Fore.RESET}{Style.RESET_ALL}")
        # Save results to a file
        with open(save_path, 'w') as file:
            file.write(json.dumps({
                'task': user_response.task_text,
                'assessment': complete_assessment_response,
                'cache_accuracy': cache_accuracy,
                'cache_knowledge': cache_knowledge,
                'cache_focus': cache_focus,
                'cache_independence': cache_independence,
                'cache_factuality': cache_factuality
            }))

    print(f"{Fore.CYAN}{Style.BRIGHT}Complete assessment response:{Fore.RESET}{Style.RESET_ALL}",
          complete_assessment_response)

    return complete_assessment_response


def is_candidate_viable(candidate_id: str, cycles: int = 3):
    # Input: filename (id)
    # Technically this algorithm is redundant to summary,
    # but it's very difficult to get both the final filtering response and the summary in one response reliably.
    # Because of the simplicity of this response, and it's importance, this vote will be cast at least 5 times,
    # the result will depend on the majority of vote.
    # For 99% of candidates, the vote will be unanimous, the rest is on the margin either way.

    filtering_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a hiring manager."
                   "Your job is to determine if this candidate meets the minimum criteria."
                   "You are presented with summarized performance of this candidate."
                   "Candidate is good if he is truthful, and offers some potential."
                   "Candidate is bad when he lies, is incompetent or clueless."
                   "Respond with a GOOD or BAD response, DO NOT add any unnecessary text."
                   "Response has to be VERY VERY SHORT, reply with ONLY 'good' or 'bad'."),
        ("user", "General candidate summary: ```{assessment}```"
                 "Candidate knowledge: ```{cache_knowledge}```"
                 "Candidate truthfulness: ```{cache_factuality}```")
    ])

    chain = (
        filtering_prompt |
        basic_llm |
        output_parser
    )

    # load candidate file
    with open(f"data/summaries/{candidate_id}.json", 'r') as file:
        # used: 'assessment', 'cache_knowledge', 'cache_factuality'
        user_data_dict = json.loads(file.read())
        print(f"{Fore.YELLOW}{Style.BRIGHT}user_file:{Fore.RESET}{Style.RESET_ALL}", user_data_dict)

    user_score = 0

    for _ in range(0, cycles+1):
        vote_result = chain.invoke(user_data_dict).lower()
        if 'good' in vote_result:
            user_score += 1
        if 'bad' in vote_result:
            user_score -= 1

    viability_result = True if user_score > 0 else False

    print(f"{Fore.CYAN}{Style.BRIGHT}Candidate:{Fore.RESET}{Style.RESET_ALL}", candidate_id,
          f"{Fore.CYAN}{Style.BRIGHT}viability:{Fore.RESET}{Style.RESET_ALL}", 'high' if viability_result else 'low',
          f"{Fore.CYAN}{Style.BRIGHT}score:{Fore.RESET}{Style.RESET_ALL}", user_score)

    return viability_result


def get_summarized_candidates() -> list:
    # all unfiltered candidates
    return list(map(separate_id, os.listdir('data/summaries')))


def get_raw_candidates() -> list:
    # this one is useless for the classic pipeline without tasks being known any other way
    return list(map(separate_id, os.listdir('data/videos')))


def filter_summarized_candidates() -> int:
    # Filter any candidates who are not viable for specified position regardless of their relative attractiveness.
    # This function will eliminate any lying, clueless and unwilling to work candidates.
    # This is why this function also takes care of physical filesystem interactions and not only opinion creation.
    candidate_list = get_summarized_candidates()
    filtered_count = 0
    for candidate_id in candidate_list:
        if not is_candidate_viable(candidate_id):
            shutil.move(f"data/summaries/{candidate_id}", f"data/rejections/{candidate_id}")
            filtered_count += 1

    print(f"{Fore.CYAN}{Style.BRIGHT}Filtered{Fore.RESET}{Style.RESET_ALL}", filtered_count,
          f"{Fore.CYAN}{Style.BRIGHT}candidates{Fore.RESET}{Style.RESET_ALL}")
    return filtered_count
