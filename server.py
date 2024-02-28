from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import assessment

app = FastAPI()


class VideoData(BaseModel):
    task_id: str
    recruitment_id: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(f"client/build/index.html", 'r') as file:
        return HTMLResponse(content=file.read(), status_code=200)


@app.post("/candidate/upload")
async def update_item(video: UploadFile = File(...), task_id: str = Form(...), recruitment_id: str = Form(...)):

    with open(f"data/videos/{video.filename}", "wb") as buffer:
        contents = await video.read()
        # buffer.write(contents)

    return {"video_task_id": task_id, "video_recruitment_id": recruitment_id,
            "video_filename": video.filename, "video_size": video.size}


# TODO: people will be selected from the list, by default all but a few may be chosen as well
@app.post("/manager/start_summarizing")
async def start_summarizing():
    assessment.summarize_candidates([])
    return {"response": "summarized filtering started"}


@app.post("/manager/start_filtering")
async def start_filtering():
    assessment.filter_summarized_candidates()
    return {"response": "summarized filtering started"}
