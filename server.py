from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class VideoInput(BaseModel):
    task_id: str
    recruitment_id: str


@app.get("/")
def read_root():
    with open(f"client/build/index.html", 'r') as file:
        return HTMLResponse(content=file.read(), status_code=200)


@app.put("/candidate/upload")
def update_item(video: VideoInput):
    return {"video_task_id": video.task_id, "video_recruitment_id": video.recruitment_id}
