---
name: new-model
description: Scaffold a new zou SQLAlchemy model with migration, CRUD blueprint, route registration and tests, following the patterns from CLAUDE.md.
disable-model-invocation: true
---

# New zou model

Use this skill to add a full new model to zou. Ask the user for:

1. **Model name**: PascalCase (e.g. `SalaryScale`). Table name derives automatically (snake_case).
2. **Columns**: name, type, nullable/default, unique, FKs. New columns must be nullable or defaulted (one-way migrations in production).
3. **Permission levels**: who can read, who can create/update/delete. Default: read for all logged-in users, write for admin.
4. **Caching**: does a service memoize reads of this model? If yes, plan invalidation in `post_update`/`post_delete` hooks.

## Workflow

1. **Model** at `zou/app/models/<snake_name>.py`, inheriting `db.Model, BaseMixin, SerializerMixin`. `BaseMixin` already provides `id`, `created_at`, `updated_at`: do not redeclare them.
2. **Migration**: `~/.virtualenvs/zou/bin/zou migrate-db --message "Add <snake_name> table"`, then read the generated file in `zou/migrations/versions/`.
3. **Run the migration-reviewer agent** on the generated migration before going further.
4. **CRUD blueprint** at `zou/app/blueprints/crud/<snake_name>.py` extending `BaseModelsResource` / `BaseModelResource`. Override permission hooks (`check_read_permissions`, `check_create_permissions`, `check_update_permissions`, `check_delete_permissions`) and, if the model is project-scoped, `add_project_permission_filter(query)`.
5. **Register routes** in `zou/app/blueprints/crud/__init__.py`: import the two resource classes and append to the `routes` list (kebab-case path):
   ```python
   ("/data/<kebab-names>", <Name>sResource),
   ("/data/<kebab-names>/<instance_id>", <Name>Resource),
   ```
6. **Tests** at `tests/blueprints/crud/test_<snake_name>s.py` following the CRUD test pattern (get list, get one + 404, create, update, delete).
7. **Run the tests**: `DB_DATABASE=zoudb-test ~/.virtualenvs/zou/bin/python -m pytest tests/blueprints/crud/test_<snake_name>s.py -v`.
8. **Remind the user about cross-repo ripple**: gazu wrapper (`all_*`/`get_*`/`new_*`/`update_*`/`remove_*`), kitsu store module if the UI surfaces it, and the model reference page in kitsu-developer-documentation. The `cross-repo-ripple` skill covers the checklist.

## Templates

### Model (`zou/app/models/<snake_name>.py`)

```python
from sqlalchemy_utils import UUIDType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class <Name>(db.Model, BaseMixin, SerializerMixin):
    """
    <One-line description of what this model represents.>
    """

    name = db.Column(db.String(80), nullable=False)
    project_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("project.id"),
        index=True,
    )
```

### CRUD blueprint (`zou/app/blueprints/crud/<snake_name>.py`)

```python
from zou.app.models.<snake_name> import <Name>
from zou.app.blueprints.crud.base import (
    BaseModelResource,
    BaseModelsResource,
)


class <Name>sResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, <Name>)

    def check_read_permissions(self, options=None):
        return True


class <Name>Resource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, <Name>)

    def check_read_permissions(self, instance):
        return True
```

If a service memoizes reads of this model, add `post_update` / `post_delete` hooks that clear the cache (see `crud/software.py` for the pattern), then run the cache-invalidation-reviewer agent on the result.

### Test (`tests/blueprints/crud/test_<snake_name>s.py`)

```python
from tests.base import ApiDBTestCase

from zou.app.models.<snake_name> import <Name>
from zou.app.utils import fields


class <Name>TestCase(ApiDBTestCase):
    def setUp(self):
        super().setUp()
        self.generate_data(<Name>, 3)

    def test_get_<snake_name>s(self):
        <snake_name>s = self.get("data/<kebab-names>")
        self.assertEqual(len(<snake_name>s), 3)

    def test_get_<snake_name>(self):
        instance = self.get_first("data/<kebab-names>")
        instance_again = self.get(f"data/<kebab-names>/{instance['id']}")
        self.assertEqual(instance, instance_again)
        self.get_404(f"data/<kebab-names>/{fields.gen_uuid()}")

    def test_create_<snake_name>(self):
        data = {"name": "test"}
        instance = self.post("data/<kebab-names>", data)
        self.assertIsNotNone(instance["id"])

    def test_update_<snake_name>(self):
        instance = self.get_first("data/<kebab-names>")
        self.put(f"data/<kebab-names>/{instance['id']}", {"name": "updated"})

    def test_delete_<snake_name>(self):
        instance = self.get_first("data/<kebab-names>")
        self.delete(f"data/<kebab-names>/{instance['id']}")
        self.get_404(f"data/<kebab-names>/{instance['id']}")
```

## Conventions

- UUID PKs and FKs use `UUIDType(binary=False)`, never `String(36)`.
- FK columns are named `<table>_id`; M2M link tables `<table1>_<table2>_link`.
- New columns nullable or defaulted; the migration-reviewer agent enforces this.
- f-strings only in new code; docstring `"""` on their own lines.
- Black line-length 79; the auto-format hook runs on save.
