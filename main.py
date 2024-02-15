# InterVue is already taken, find a different name :)
# | Interly | FlyView | SpeedVue | TopInterview | GpVue
from colorama import init as colorama_init

from assessment import StandardTaskResponse, generate_response_summarization, StandardTask

colorama_init()

filename = "data/videos/interview_practice3.webm"

task_2 = 'What was the greatest achievement in your career?'
task_3 = 'What was a difficult situation you were in? How did you deal with it?'

example_task = StandardTask(task_3)

example_task_response = StandardTaskResponse(
    file_name=filename,
    task_text=example_task.task_text,
)

generate_response_summarization(example_task_response)
