# InterVue is already taken, find a different name :)
# This file is the server part of this project
# | Interly | FlyView | SpeedVue | TopInterview | GpVue
from colorama import init as colorama_init

from assessment import StandardTaskResponse, generate_response_summarization, get_raw_candidates, \
    get_summarized_candidates, filter_summarized_candidates

import uvicorn

colorama_init()

# NOTE: until we formalize to use a single file type for the input, we will keep on specifying the whole filename,
#       instead of just an identifier
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
    generate_response_summarization(response, overwrite=False)

# is_candidate_viable('interview_practice1', cycles=1)
# is_candidate_viable('interview_practice2', cycles=1)
# is_candidate_viable('interview_practice3', cycles=1)
# is_candidate_viable('interview_practice4', cycles=1)

# is_candidate_viable('interview_practice2', cycles=3)

print(get_summarized_candidates())
print(get_raw_candidates())

filter_summarized_candidates()

# as this is currently a testing file, we use a different method of running this web server,
# feel free to uncomment this line to run the webserver straight from main.
"""
if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
"""
