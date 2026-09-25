# Earth and Environmental Computing Course Hub

This reusable, student-facing course repository introduces computational
methods for Earth and environmental science. It includes a course website,
lecture slide decks, student lab notebooks, final-project templates, classroom
datasets, and the code needed to run the notebooks.

The website is published with GitHub Pages from `index.html`.

## Student setup

```bash
conda env create -f environment.yml
conda activate earth-course
python scripts/download_data.py
python scripts/clean_data.py
jupyter lab
```

Students who prefer `pip` can use `requirements.txt`. Students who work in VS
Code on their own computer can follow the step-by-step guide in
`vscode-setup.html`, which the course site links from its setup section.

## Public-content boundary

This repository is a student distribution copy. Instructor notebooks, solution
keys, teaching notes, course-production sources, draft documents, and temporary
files are kept outside this repository. `STUDENT_CONTENT_MANIFEST.md` records
the allowed public content. The Pages workflow runs a path-based safety check
before every deployment.

## Repository layout

- `materials/slides/`: student-facing HTML slide decks.
- `notebooks/`: individual labs, group labs, debrief guidance, and project templates.
- `data/processed/`: stable classroom datasets used by the notebooks.
- `src/`: reusable scientific-computing functions.
- `scripts/`: student-facing data preparation and Lab 4 files.
- `assets/`: course website styles.

The site uses institution-neutral language and a week-based schedule so it can
be adapted to different academic calendars. Course materials remain under the
copyright of their author unless a separate license is added.
