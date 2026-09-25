# Student Content Manifest

Only student-facing material belongs in this public repository.

## Allowed content

- Course website files: `index.html`, `vscode-setup.html`, `assets/`, and `.nojekyll`.
- Public-repository documentation: `README.md`, `syllabus.md`, and this manifest.
- Student lecture slides: `materials/slides/*.html`.
- Student notebooks and templates: `notebooks/`.
- Classroom-ready data and source documentation: `data/`.
- Code required by student notebooks: `src/` and the selected files in `scripts/`.
- Environment files: `environment.yml` and `requirements.txt`.
- Student-facing figures: `figures/`.
- GitHub Pages automation: `.github/workflows/`.

## Never publish here

- Instructor notebooks or teaching notes.
- Solutions, answer keys, hidden grading guidance, or expected student outputs.
- Draft syllabi, comments, tracked revisions, and document-production folders.
- Slide-generation source files, speaker notes, and inspection artifacts.
- Temporary files, caches, local environments, credentials, or private data.

The deployment safety check blocks common private-content path patterns and any
top-level item outside the allowlist.
