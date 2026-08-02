# SEES:4100 Computation in the Earth and Environment

This is the public, student-facing course repository for Fall 2026. It includes
the course website, lecture slide decks, student lab notebooks, final-project
templates, classroom datasets, and the code needed to run the notebooks.

The website is published with GitHub Pages from `index.html`.

## Student setup

```bash
conda env create -f environment.yml
conda activate sees4100
python scripts/download_data.py
python scripts/clean_data.py
jupyter lab
```

Students who prefer `pip` can use `requirements.txt`.

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
- `src/sees4100/`: reusable scientific-computing functions.
- `scripts/`: student-facing data preparation and Lab 4 files.
- `assets/`: course website styles.

Course materials remain under the copyright of their author unless a separate
license is added.
