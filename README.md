# Github Events API Project

This project is part of the DataMole hiring process for Python Data Engineer.

## Overview

The goal of this application is to be able request data from Github API. Those data are information
about Github events happening in configured repositories. Second part is to have API endpoints to
get statistics - average time difference between consequtive events for given repository and event type.
They are averaged either over 7 days or 500 events, which of those will happen first.

## Setup

- this project uses Python 3.11.9, see [.python-version](.python-version) file
- for managing virtual environments and dependencies, please install [poetry](https://python-poetry.org/docs/#installation)
  - to install dependencies in your virtual environmnet you can run `poetry install`; more info [here](https://python-poetry.org/docs/cli/#install)
- for authentication to Github API, please create your personal access token by [those instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)
    - create `.env` file in main directory and store this token there; see [template.env](template.env) file for example how it should look like


## How to run

This application has two parts:
1. download events data from Github API about configured repositories and calculate statistics
2. run application to serve API endpoints

### Pre-requisities
- do the setup as described in [Setup](#setup)
- define requested repositories in [repository.yaml](repositories.yaml) file as list of dict with keys `owner` and `name`
  - e.g. for this repository the `owner` is "IvaMarosov" and `name` is "github_events_api"


### Download data from Github API

- main script for this part is [`download_data.py`](download_data.py)
- run it with `python download_data.py`
- as part of the script, there is local SQLite database created in `data` folder with name `sql_model.db`
  - here will be stored all information about repositories, events and statistics

### Open FastAPI application

- main script is [`api_app.py`](api_app.py)
- open the application with `uvicorn api_app:app`
- this will run the application in your local server `https://127.0.0.1:8000`
- on this route you can send requests for statistics data; see [API Documentation](#api-documentation) part

## API Documentation

This project uses Swagger UI for API documentation.
The Swagger UI provides an interactive interface to explore and test the API endpoints.

To access the documentation you can:

1. Run the FastAPI application
2. Open a web browser and navigate to `http://127.0.0.1:8000/docs` 
or `http://127.0.0.1:8000/redoc` (assuming you didn't change the host and port where 
the application runs).

You can also check OpenAPI v3 API documentation in [YAML](docs/openapi.yaml) and [JSON](docs/openapi.json) file format.

## Developer tools

There are some basic developer tools implemented for easier contribution:

- run `make help` in your terminal to see list of them
  - `make lint` - runs complete pre-commit linting 
  - `make test` - automatically runs all tests in [`tests`](tests) folder
  - `make check` - run both linting and tests

## Limitations and future work
- getting data from Github API is still done manually - to download them regularly you would need to implement
some cron or scheduler
- application with API endpoints runs locally, but could be deployed remotelly
- statistics are calculated only for current data, we do not store history
- the 7 day average is calculated from the latest date for given repository and event type, not from current date
- add unit tests for database functions and API endpoints
- add integration tests for both main scripts
