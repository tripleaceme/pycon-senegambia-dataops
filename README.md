# DataOps in Practice: Applying DevOps Principles to Modern Data Platforms

### PyCon Senegambia 2026 — Complete DataOps Workshop Outline

| | |
|---|---|
| **Format** | Hands-on workshop, 120 minutes |
| **Level** | Intermediate |
| **Audience** | Python developers, data engineers, analytics engineers and software engineers |
| **Location** | Dakar, Senegal |

This repository is the **starter**. It holds a working Python pipeline that loads Bluebikes trips into Snowflake. Someone has to run it by hand, and nothing checks the code or the data. During the workshop we turn it into an automated, tested and observable data workflow, one practice at a time.

Please complete the [setup steps](#7-before-the-workshop) before you arrive. The workshop time goes on DataOps, not on installing Python.

---

## Contents

1. [The problem](#1-the-problem)
2. [What we are going to do](#2-what-we-are-going-to-do)
3. [The data](#3-the-data)
4. [Technology stack](#4-technology-stack)
5. [What is in this repository](#5-what-is-in-this-repository)
6. [Architecture](#6-architecture)
7. [Before the workshop](#7-before-the-workshop)
8. [What we build in the live session](#8-what-we-build-in-the-live-session)
9. [Workshop agenda](#9-workshop-agenda)
10. [What your repository looks like at the end](#10-what-your-repository-looks-like-at-the-end)
11. [Troubleshooting](#11-troubleshooting)
12. [Data source and licence](#12-data-source-and-licence)

---

## 1. The problem

You work on the data team of a bike-sharing company. Every day, a third-party provider sends a CSV file with the previous day's trips. The business uses those trips in Snowflake to plan station capacity, move bikes between stations and report on usage.

A colleague wrote a Python script that reads the CSV, cleans it up and loads it into Snowflake. It works. But:

- **Someone has to run it by hand.** If that person is sick or on leave, the data stops.
- **The Snowflake password is written in the code.** One careless commit and it is on GitHub.
- **Changes go straight in.** There are no branches, no reviews and no record of who changed what or why.
- **Nothing tests the code.** A small mistake in the duration calculation would reach every dashboard.
- **Nothing checks the data.** If the provider sends a file with missing stations or broken timestamps, it is loaded anyway.
- **Running it twice loads everything twice.** There is no protection against duplicates.
- **Nobody knows when it fails.** There are no logs and no alerts. You find out when a stakeholder asks why the numbers look wrong.



## 2. What we are going to do

We apply DevOps principles to this data pipeline. DevOps changed how software teams ship code: 
- Version control
- Automated testing
- Continuous integration and monitoring. 

DataOps applies the same ideas to data, with one addition. In a data pipeline, both the **code** and the **data** can be wrong, so we check both.

| Before (this starter) | After (end of the workshop) |
|---|---|
| Run by hand on a laptop | Runs on a daily schedule, or on demand from GitHub |
| Credentials written in the code | python-decouple and a `.env` file locally, GitHub Secrets in the cloud |
| Changes made directly | Feature branches and pull requests |
| No tests | pytest unit tests for the transformation logic |
| Any file gets loaded | Quality checks reject a bad file before it reaches Snowflake |
| No automated checks on code | GitHub Actions runs Ruff and pytest on every pull request |
| File read from the laptop | Files picked up from Backblaze B2 cloud storage and archived after processing |
| Reruns create duplicates | Reruns are safe |
| `print()` statements | Structured logs, run summaries and failure alerts |

## 3. The data

We use **trip records from [Bluebikes](https://bluebikes.com/system-data)**, the public bike-share system in Metro Boston. Bluebikes publishes its full trip history as monthly files in a [public bucket](https://s3.amazonaws.com/hubway-data/index.html).

The file in this repository, `data/bluebikes_trips_2024_03_28.csv`, contains **every ride that started on Thursday 28 March 2024**: 3,605 trips. 

The source file has 13 columns. Our pipeline will use five of them and calculates a sixth because of limited time:

| Bluebikes column | Our column | Meaning |
|---|---|---|
| `ride_id` | `trip_id` | Unique ID for the trip |
| `started_at` | `started_at` | When the trip started (local Boston time) |
| `ended_at` | `ended_at` | When the trip ended |
| `start_station_name` | `start_station` | Station where the bike was taken |
| `end_station_name` | `end_station` | Station where the bike was returned |
| `calculated` | `duration_minutes` | Calculated: `ended_at` minus `started_at`, in minutes |


## 4. Technology stack

Everything below is free for this workshop, either open source or on a free tier or trial.

| Layer | Tool | What it does in this workshop |
|---|---|---|
| Data | Bluebikes trip history | source data |
| Language | Python 3.11+ | The pipeline |
| Processing | Pandas | Reads, selects, renames and transforms the trips |
| Warehouse | Snowflake | Stores the curated `BIKE_TRIPS` table |
| Cloud storage | Backblaze B2 | Holds incoming files and archives processed and failed ones |
| Version control | Git and GitHub | Branches, commits and pull requests |
| Configuration | python-decouple | Reads settings from a local `.env` file or from environment variables |
| Secrets in the cloud | GitHub Secrets | Credentials for scheduled runs |
| Formatting and linting | Ruff | Keeps code consistent and catches common mistakes |
| Unit testing | pytest | Checks the transformation logic |
| Data quality | Python and Pandas validation functions | Checks each incoming file at runtime |
| CI | GitHub Actions | Runs Ruff and pytest on every pull request |
| Scheduling | GitHub Actions | Runs the pipeline daily and on demand |
| Logging | Python `logging` | Structured run logs |
| Monitoring | GitHub Actions run history and job summaries | Shows what each run did |
| Notifications | Email (instructor demo only) | Alerts on failures and missing files |


## 5. What is in this repository

```
pycon-senegambia-dataops/
├── data/
│   └── bluebikes_trips_2024_03_28.csv   Bluebikes trips for one day (3,605 rows)
├── src/
│   ├── pipeline.py                      Entry point: read → transform → load
│   ├── transform.py                     Selects and renames 5 columns, adds duration_minutes
│   └── load.py                          Creates BIKE_TRIPS in Snowflake and appends the rows
├── scripts/
│   └── dowload_data.py                  How the data file was produced (you don't need to run it)
├── requirements.txt                     pandas, snowflake-connector-python
├── .gitignore
└── README.md
```

**What the pipeline does today**

1. Takes the Snowflake connection details written at the top of `src/load.py`.
2. Reads the CSV into a Pandas DataFrame.
3. Keeps five columns, renames them, converts the timestamps and calculates `duration_minutes`.
4. Creates `BIKE_TRIPS` in Snowflake if it does not exist and appends the rows.


## 6. Architecture

By the end of the workshop there are two separate flows. One looks after the **code** and one looks after the **data**. Both run on GitHub Actions.

```
A. CODE LIFECYCLE  (.github/workflows/ci.yml)

   feature branch ──► pull request ──► Ruff + pytest ──► merge to main
                                       (must pass)       (approved code)
                                                              │
B. DATA LIFECYCLE  (.github/workflows/run-pipeline.yml)       │ runs the code in main
                                                              ▼
   daily schedule / manual trigger ──► Backblaze B2: incoming/ ──► processing/
                                                              │
                                     Python: validate ──► transform ──► load to Snowflake
                                                              │
                                    processed/ (success)  or  failed/ (rejected)
                                                              │
                                    logs · run summary · alert (instructor demo)
```



---

## 7. Before the workshop


### What you need

- [ ] A laptop with **Python 3.11 or newer** (`python --version`)
- [ ] **Git** (`git --version`)
- [ ] A **GitHub** account
- [ ] A code editor, such as VS Code
- [ ] A **Snowflake** account. The [30-day free trial](https://signup.snowflake.com/) is enough. Choose any cloud and region.
- [ ] A **Backblaze B2** account ([free sign-up](https://www.backblaze.com/sign-up/cloud-storage), 10 GB free). You only need the account. We create the bucket together in section 6.

### Step 1 — Get the code

Open [github.com/tripleaceme/pycon-senegambia-dataops](https://github.com/tripleaceme/pycon-senegambia-dataops) and click **Fork** to copy it to your own GitHub account. Then clone your fork:

```bash
git clone https://github.com/<your-username>/pycon-senegambia-dataops.git
cd pycon-senegambia-dataops
```

You need your own fork because you will push branches, open pull requests and run GitHub Actions on it.

### Step 2 — Create a virtual environment and install

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 3 — Prepare Snowflake

Log in to Snowsight (the Snowflake web UI), open a new **SQL worksheet** and run:

```sql
CREATE DATABASE IF NOT EXISTS DATAOPS_WORKSHOP;
CREATE SCHEMA IF NOT EXISTS DATAOPS_WORKSHOP.PUBLIC;
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
```

Trial accounts already have `COMPUTE_WH`. The last statement does nothing if it exists.

Then collect your **account identifier**. In Snowsight, click your name in the bottom left, then **Account → View account details**. Copy the value labelled *Account identifier*. It looks like `ORGNAME-ACCOUNTNAME`.

### Step 4 — Add your connection settings

Open `src/load.py`. The Snowflake connection details are written at the top of the file:

```python
SNOWFLAKE_ACCOUNT = "your_account_identifier"
SNOWFLAKE_USER = "your_username"
SNOWFLAKE_PASSWORD = "your_password"
SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
SNOWFLAKE_DATABASE = "DATAOPS_WORKSHOP"
SNOWFLAKE_SCHEMA = "PUBLIC"
SNOWFLAKE_ROLE = "ACCOUNTADMIN"
```

Replace the placeholders with your own values and save the file.

> **Do not commit `src/load.py` after you add your password.** Your fork is public, so a commit would publish the password. Writing credentials in the code is the first problem we fix in the workshop. Until then, keep the change on your laptop only.

### Step 5 — Run the pipeline

```bash
python -m src.pipeline
```

Expected output:

```
Read 3,605 rows from bluebikes_trips_2024_03_28.csv
Loaded 3,605 rows into DATAOPS_WORKSHOP.PUBLIC.BIKE_TRIPS
Note: every run appends again. We fix that during the workshop.
```

### Step 6 — Check the result in Snowflake

```sql
SELECT COUNT(*) FROM DATAOPS_WORKSHOP.PUBLIC.BIKE_TRIPS;          -- 3605

SELECT *
FROM DATAOPS_WORKSHOP.PUBLIC.BIKE_TRIPS
ORDER BY STARTED_AT
LIMIT 10;
```

**You are ready if** the count is 3,605 and you can see the `DURATION_MINUTES` column. If the count is higher, you ran the pipeline more than once. Run `TRUNCATE TABLE DATAOPS_WORKSHOP.PUBLIC.BIKE_TRIPS;` and run it again.

If you get stuck, see [Troubleshooting](#11-troubleshooting). If you still cannot get it working, come anyway. You can follow the instructor's screen and catch up later with the finished code.

---

## 8. What we build in the live session

Seven sections, in this order. Each one fixes one of the problems listed in [section 1](#1-the-problem). Code for each step is provided, so the time goes on understanding the change, not typing it.

### 01 · Configuration management

**Problem it solves:** credentials and settings live next to the code, and the same code cannot run on your laptop and in the cloud without editing it.

**What we do**
- Look at the ways teams keep settings out of code. Locally: environment variables, `.env` files with `python-dotenv` or `python-decouple`, and config files such as JSON, YAML or INI. In the cloud: GitHub Secrets, AWS Secrets Manager, Azure Key Vault, Google Secret Manager and HashiCorp Vault.
- Move the Snowflake values out of `src/load.py` into a `.env` file that Git ignores.
- Read them in a new `src/config.py` with **python-decouple**: `config("SNOWFLAKE_ACCOUNT")`. It reads `.env` on your laptop and environment variables in GitHub Actions, so the same code works in both places.
- Add `.env.example` so others know which settings to fill in, without seeing your values.
- Look at how the same names become **GitHub Secrets** when the pipeline runs in the cloud.

**Outcome:** the pipeline runs anywhere without changing the source code, and no secret is ever committed.

### 02 · Git and version control

**Problem it solves:** changes go straight in with no review and no history of why.

**What we do**
- Create a feature branch, make a change, commit it with a clear message and push it.
- Open a pull request on GitHub and look at the review process.
- Talk about why every change to a data pipeline should be traceable to a person and a reason.

**Outcome:** every change is proposed, reviewed and recorded before it reaches `main`.

### 03 · Automated unit testing

**Problem it solves:** a mistake in the transformation logic would go unnoticed until a dashboard shows wrong numbers.

**What we do**
- Introduce `pytest` and write tests for `transform_trips()` using small hand-written DataFrames with known answers.
- Test that the right columns are selected and renamed, and that `duration_minutes` is calculated correctly.
- Break the duration calculation on purpose, watch the test fail, then fix it.

**Outcome:** we can prove the transformation does what we think it does, every time the code changes.

### 04 · Runtime data quality

**Problem it solves:** the code can be correct and the data can still be wrong. Unit tests check the code. They never see tomorrow's file.

**What we do**
- Write validation functions in `quality.py` that run on every incoming file before anything is loaded:
  - required columns are present
  - `trip_id` is never empty
  - `trip_id` is unique
  - timestamps can be parsed
  - a trip does not end before it starts
  - station names are present
- Decide which failures are **critical**. If any critical check fails, the whole file is rejected and nothing is loaded.
- Run the checks against the real Bluebikes file and look at what they find.

**Outcome:** bad data is stopped before it reaches Snowflake, and we know exactly why.

### 05 · CI/CD with GitHub Actions

**Problem it solves:** checks only help if someone remembers to run them.

**What we do**
- Create `.github/workflows/ci.yml`. It runs on every pull request:
  1. `ruff format --check` for consistent formatting
  2. `ruff check` for lint errors
  3. `pytest` for the unit tests
- Open a pull request with a failing test and see the red check. Fix it and see it pass.
- Make the checks *required*, so a pull request cannot be merged while they fail.
- Look at continuous integration, continuous delivery and continuous deployment, and why merging to `main` is our release.

**Outcome:** no code reaches `main` without passing automated checks.

### 06 · Automated pipeline execution

**Problem it solves:** the pipeline only runs when someone remembers to run it, from a file on their laptop.

**What we do**
- Create your own Backblaze B2 bucket with four folders (prefixes):

  ```
  incoming/     the provider drops new files here
  processing/   a file is moved here while the pipeline works on it
  processed/    the original file is archived here after a successful load
  failed/       a rejected file is moved here for investigation
  ```

- Add `storage.py` so the pipeline finds new files in `incoming/` and moves them through the folders.
- Store the Snowflake and B2 credentials as **GitHub Secrets**.
- Create `.github/workflows/run-pipeline.yml`, which runs once a day and can also be started by hand with the **Run workflow** button.
- Make reruns safe, so a file that has already been loaded is skipped rather than loaded twice.

What the pipeline does in each case:

| Situation | What happens |
|---|---|
| New file in `incoming/` | Validate, load, move to `processed/` |
| No new file | Log `NO_DATA` and finish successfully |
| File fails a critical quality check | Load nothing, move to `failed/`, mark the run as failed |
| Snowflake load fails | Keep the file for investigation, mark the run as failed |
| File was already processed | Skip it and log that it was skipped |

**Outcome:** new data is processed without anyone running a script.

### 07 · Logging, monitoring and notifications

**Problem it solves:** when the pipeline fails, nobody knows, and when it succeeds, nobody can tell what it did.

**What we do**
- Replace `print()` with Python's `logging` module, so every message has a time, a level and context.
- Record a summary for every run: file name, status, rows read, rows loaded, checks failed and duration.
- Write that summary to the GitHub Actions **job summary**, so it is visible on the run page.
- Use the Actions run history as a simple monitoring view: what ran, when, and whether it worked.
- **Instructor demo:** send an email alert when a run fails or when the day's file has not arrived.

**Outcome:** every run explains itself, and failures reach a person.

## 9. Workshop agenda

| Time | Section |
|---|---|
| 0–10 min | Introduction, the business problem, check everyone's starter runs |
| 10–15 min | What DevOps is, what DataOps is, and how they relate |
| 15–25 min | 01 · Configuration management |
| 25–35 min | 02 · Git and version control |
| 35–50 min | 03 · Automated unit testing |
| 50–65 min | 04 · Runtime data quality |
| 65–85 min | 05 · CI/CD with GitHub Actions |
| 85–105 min | 06 · Automated pipeline execution with Backblaze B2 |
| 105–115 min | 07 · Logging, monitoring and notifications |
| 115–120 min | Recap and questions |

## 10. What your repository looks like at the end

```
pycon-senegambia-dataops/
├── .github/
│   └── workflows/
│       ├── ci.yml                  Ruff + pytest on every pull request
│       └── run-pipeline.yml        Daily and manual pipeline runs
├── data/
│   └── bluebikes_trips_2024_03_28.csv
├── src/
│   ├── pipeline.py
│   ├── transform.py
│   ├── load.py                     Now safe to rerun
│   ├── config.py                   Settings read with python-decouple
│   ├── quality.py                  Runtime data quality checks
│   ├── storage.py                  Backblaze B2 file handling
│   ├── logging_config.py           Structured logging
│   └── notifications.py            Email alerts (instructor demo)
├── tests/
│   ├── test_transform.py
│   └── test_quality.py
├── .env.example
├── pyproject.toml                  Ruff and pytest settings
├── requirements.txt
└── README.md
```

## 11. Troubleshooting

| Problem | What to check |
|---|---|
| `python` not found, or the version is below 3.11 | On macOS and Linux, try `python3`. Install 3.12 from [python.org](https://www.python.org/downloads/). |
| `pip install` fails building a package from source | Your Python version is probably too old or too new for a prebuilt wheel. Use Python 3.11 or 3.12. |
| `ModuleNotFoundError: No module named 'src'` | Run the command from the repository root as `python -m src.pipeline`, not `python src/pipeline.py`. |
| Error mentioning `your_account_identifier` | You have not replaced the placeholders at the top of `src/load.py` (step 4). |
| `250001: Could not connect` or an account not found error | Check the `account` value. Use the account identifier (`ORGNAME-ACCOUNTNAME`), not the full URL. |
| Incorrect username or password | Log in to Snowsight with the same values to confirm them. |
| Login rejected because MFA is required | Snowflake increasingly blocks password-only logins from scripts. In Snowsight, go to your user profile, generate a **programmatic access token** and put it in `SNOWFLAKE_PASSWORD`. |
| `Database 'DATAOPS_WORKSHOP' does not exist` | Run the SQL in step 3, or check the `role` has access to it. |
| `No active warehouse selected` | Check the `warehouse` name. Run `SHOW WAREHOUSES;` to see what exists. |
| Row count is a multiple of 3,605 | You ran the pipeline more than once. The starter appends on every run. Truncate the table and run it once. |
