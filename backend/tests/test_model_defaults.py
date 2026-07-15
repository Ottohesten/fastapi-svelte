import uuid
from datetime import timezone

import pytest

from app.models import GameSession, Recipe


@pytest.mark.no_db
@pytest.mark.parametrize("model", [Recipe, GameSession])
def test_created_at_uses_a_timezone_aware_factory(
    model: type[Recipe] | type[GameSession],
):
    field = model.model_fields["created_at"]

    assert field.default_factory is not None

    instance = model(title="Test", owner_id=uuid.uuid4())
    assert instance.created_at.tzinfo is timezone.utc
