---
name: new-endpoint
description: Scaffold a new zou REST API endpoint following the blueprint + Pydantic + test pattern from CLAUDE.md.
disable-model-invocation: true
---

# New zou endpoint

Use this skill to scaffold a new Flask endpoint in zou. Ask the user for:

1. **Domain** — the blueprint package (e.g. `tasks`, `assets`, `playlists`). If new, you will create `zou/app/blueprints/<domain>/`.
2. **Route path** — e.g. `/data/entities/<entity_id>/tasks`.
3. **HTTP method(s)** — GET, POST, PUT, DELETE.
4. **Request body shape** (if POST/PUT) — fields, types, required vs optional.
5. **Permission level** — `check_admin_permissions`, `check_manager_permissions`, `check_at_least_supervisor_permissions`, `user_service.check_project_access`, or custom.

## Workflow

1. **Locate or create the blueprint package** at `zou/app/blueprints/<domain>/` with `__init__.py`, `resources.py`, `schemas.py`.
2. **Add the Resource class** in `resources.py` (one class per HTTP path). Use the template below.
3. **Add the Pydantic schema** in `schemas.py` if the route accepts a body. Use `BaseSchema` from `zou.app.utils.validation`.
4. **Register the route** in `__init__.py` `routes` list (kebab-case path).
5. **Register the blueprint** in `zou/app/api.py` if the package is new.
6. **Write tests** in `tests/<domain>/test_route_<name>.py` inheriting `ApiDBTestCase`. Cover happy path + at least one permission/validation failure.
7. **Run tests**: `DB_DATABASE=zoudb-test py.test tests/<domain>/test_route_<name>.py -v`.
8. **Remind the user** about cross-repo ripple: gazu wrapper, kitsu store method (if UI-facing), and kitsu-developer-documentation page. The `cross-repo-ripple` skill covers the checklist.

## Templates

### Resource (`resources.py`)

```python
from flask.views import MethodView
from flask_jwt_extended import jwt_required

from zou.app.blueprints.<domain>.schemas import <Name>Schema
from zou.app.services import <domain>_service, user_service
from zou.app.utils import permissions, validation


class <Name>Resource(MethodView):
    @jwt_required()
    def post(self, entity_id):
        """
        <One-line summary>
        ---
        description: <what it does>
        tags:
          - <Domain>
        parameters:
          - in: path
            name: entity_id
            required: true
            schema:
              type: string
              format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  field: {type: string}
        responses:
          201:
            description: Created
          400:
            description: Validation error
        """
        entity = <domain>_service.get_entity(entity_id)
        user_service.check_project_access(entity["project_id"])
        permissions.check_manager_permissions()
        body = validation.validate_request_body(<Name>Schema)
        result = <domain>_service.do_thing(entity, body.field)
        return result, 201
```

### Schema (`schemas.py`)

```python
from typing import List, Optional
from pydantic import Field
from zou.app.utils.validation import BaseSchema


class <Name>Schema(BaseSchema):
    field: str = Field(..., min_length=1, description="...")
    optional_field: Optional[str] = None
```

### Route registration (`__init__.py`)

```python
from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.<domain>.resources import <Name>Resource

routes = [
    ("/data/entities/<entity_id>/things", <Name>Resource),
]

blueprint = Blueprint("<domain>", "<domain>")
api = configure_api_from_blueprint(blueprint, routes)
```

### Test (`tests/<domain>/test_route_<name>.py`)

```python
from tests.base import ApiDBTestCase


class <Name>TestCase(ApiDBTestCase):
    def setUp(self):
        super().setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset_type()
        self.generate_fixture_asset()

    def test_create(self):
        path = "/data/entities/%s/things" % self.asset.id
        result = self.post(path, {"field": "x"}, 201)
        self.assertIsNotNone(result)

    def test_validation_error(self):
        path = "/data/entities/%s/things" % self.asset.id
        self.post(path, {}, 400)
```

## Conventions

- Route paths are **kebab-case** (`/data/task-statuses`, not `/data/task_statuses`).
- Pydantic v2 only for request bodies — never `reqparse`.
- Query params use `ArgsMixin` methods (`get_text_parameter`, `get_bool_parameter`).
- Services are module-level functions in `zou/app/services/<domain>_service.py`.
- Emit `events.emit("<table>:<action>", payload, project_id=...)` after mutations.
- Black line-length 79; the auto-format hook runs on save.
