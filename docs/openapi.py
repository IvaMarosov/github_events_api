import json

import yaml
from fastapi.openapi.utils import get_openapi

from api_app import API_DESCR, API_TITLE, API_VERSION, app

openapi_schema = get_openapi(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCR,
    routes=app.routes,
)


def _generate_openapi_json():
    with open("docs/openapi.json", "w") as file:
        json.dump(openapi_schema, file, sort_keys=False)


def _generate_openapi_yaml():
    with open("docs/openapi.yaml", "w") as file:
        yaml.dump(openapi_schema, file, sort_keys=False)


if __name__ == "__main__":
    _generate_openapi_json()
    _generate_openapi_yaml()
