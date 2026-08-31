"""Fail deployment when a private course path enters the public repository."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_FILES = {
    ".github/workflows/pages.yml",
    ".gitignore",
    ".nojekyll",
    "README.md",
    "STUDENT_CONTENT_MANIFEST.md",
    "assets/site.css",
    "data/README.md",
    "data/metadata/data_sources.yml",
    "environment.yml",
    "figures/grouplab01_rain_river_2019.png",
    "index.html",
    "notebooks/AI_USAGE_LOG.md",
    "notebooks/LAB_DEBRIEF_GUIDE.md",
    "notebooks/final_project/AI_USAGE_LOG.md",
    "notebooks/final_project/FinalProject01_group_proposal_template.ipynb",
    "notebooks/final_project/FinalProject02_analysis_template.ipynb",
    "notebooks/final_project/FinalProject03_presentation_outline.md",
    "notebooks/final_project/FinalProject04_individual_contribution_statement.md",
    "requirements.txt",
    "scripts/build_synthetic_spatial_data.py",
    "scripts/check_public_content.py",
    "scripts/clean_data.py",
    "scripts/download_data.py",
    "scripts/messy_streamflow_analysis.py",
    "src/earthcourse/__init__.py",
    "src/earthcourse/hydro.py",
    "src/earthcourse/io.py",
    "src/earthcourse/modeling.py",
    "src/earthcourse/plotting.py",
    "src/earthcourse/spatial.py",
    "src/earthcourse/stats.py",
    "syllabus.md",
}

ALLOWED_FILES.update(
    f"materials/slides/Week{week:02d}_slides.html"
    for week in (*range(1, 14), 15, 16)
)
ALLOWED_FILES.update(
    f"data/processed/{name}"
    for name in (
        "iowa_city_weather_daily.csv",
        "iowa_city_weather_hourly.csv",
        "iowa_river_water_quality.csv",
        "iowa_stream_sites_annual_flow.csv",
        "iowa_streamflow_daily.csv",
        "synthetic_elevation_grid.csv",
        "synthetic_soil_moisture_spatial.csv",
        "synthetic_temperature_grid.csv",
    )
)
ALLOWED_FILES.update(
    f"notebooks/individual_labs/{name}"
    for name in (
        "Lab01_setup_jupyter_first_plot.ipynb",
        "Lab02_python_basics_conditionals_loops_events.ipynb",
        "Lab04_functions_debugging_hydrologic_indices.ipynb",
        "Lab05_numpy_arrays_gridded_earth_data.ipynb",
        "Lab06_pandas_time_series_streamflow_weather.ipynb",
    )
)
ALLOWED_FILES.update(
    f"notebooks/group_labs/{name}"
    for name in (
        "GroupLab01_scientific_visualization.ipynb",
        "GroupLab02_statistics_regression_uncertainty.ipynb",
        "GroupLab03_algorithm_development_interpolation_smoothing.ipynb",
        "GroupLab04_ai_agent_scientific_coding.ipynb",
        "GroupLab05_geostatistics_semivariogram_idw.ipynb",
        "GroupLab06_simple_environmental_model_calibration.ipynb",
    )
)

BLOCKED_PARTS = {
    "instructor",
    "solutions",
    "solution",
    "teaching_notes",
    "answer_key",
    "_docx_temp",
    "_syllabus_render",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
}

def find_violations() -> list[str]:
    violations: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue

        relative_posix = relative.as_posix()
        if relative_posix not in ALLOWED_FILES:
            violations.append(f"file not on public allowlist: {relative_posix}")

        lower_parts = {part.lower() for part in relative.parts}

        if lower_parts & BLOCKED_PARTS:
            violations.append(f"blocked path: {relative.as_posix()}")

        lower_name = path.name.lower()
        if lower_name.endswith(".pptx") or lower_name.endswith(".inspect.ndjson"):
            violations.append(f"blocked file type: {relative.as_posix()}")

    return sorted(set(violations))


def main() -> int:
    violations = find_violations()
    if violations:
        print("Public-content check failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Public-content check passed: only allowlisted student content is present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
