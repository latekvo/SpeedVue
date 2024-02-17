# SpeedVue

### An AI powered hiring pipeline engine.
Put hundreds of potential job candidates through an advanced screening process in a matter of minutes.

---

### How to test:
This project is currently in the testing phase - no webui is available yet.\
To test it's functionality, create this file structure:
* data
  * videos
    * [your interview videos here]
  * audio
    * [alternative to videos]
  * web
    * [web assets, leave empty]
  * summaries
    * [cached end results of individual assessments]

In the main file, you can then choose the file to analyze by specifying it's path.

---

### How to run:
* Install and launch Ollama: `ollama serve`
* Pull the model you intend to use: `ollama pull zephyr:7b-beta-q5_K_M` (default)
* Create new environment: `conda env create -f environment.yml`
* Activate the new environment: `conda activate InterVue`
* Run: `python3 main.py`

---

### Dependencies:
This tool requires `ffmpeg`, `python 8`, `conda` and `ollma` to be installed.\
Any python-related dependencies are automatically installed via conda (see 'How to run').