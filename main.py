# InterVue is already taken, find a different name :)
# This file is the server part of this project
# | Interly | FlyView | SpeedVue | TopInterview | GpVue
from colorama import init as colorama_init

from assessment import StandardTaskResponse, generate_response_summarization, StandardTask

colorama_init()

response_list = [
    StandardTaskResponse(
        file_name='data/videos/interview_practice1.webm',
        task_text='Introduce yourself. Why should we hire you?'
    ),
    StandardTaskResponse(
        file_name='data/videos/interview_practice2.webm',
        task_text='What was the greatest achievement in your career?'
    ),
    StandardTaskResponse(
        file_name='data/videos/interview_practice3.webm',
        task_text='What was a difficult situation you were in? How did you deal with it?'
    ),
    StandardTaskResponse(
        file_name='data/videos/interview_practice4.webm',
        task_text='Introduce yourself. Why should we hire you?'
    ),
]

for response in response_list:
    generate_response_summarization(response)
