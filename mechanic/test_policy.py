from .models import Action, Autonomy
from .policy import allowed_to_execute, classify_action

def action(action_type: str) -> Action:
    return Action(id="a1", incident_id="i1", action_type=action_type, summary="test")

def test_green_is_automatic():
    a = action("restart_service")
    assert classify_action(a) is Autonomy.GREEN
    assert allowed_to_execute(a)

def test_yellow_requires_approval():
    a = action("rollback_deployment")
    assert classify_action(a) is Autonomy.YELLOW
    assert not allowed_to_execute(a)
    assert allowed_to_execute(a, approval_granted=True)

def test_red_is_never_allowed():
    a = action("destroy_data")
    assert classify_action(a) is Autonomy.RED
    assert not allowed_to_execute(a, approval_granted=True)

def test_unknown_defaults_to_approval():
    assert classify_action(action("something_new")) is Autonomy.YELLOW
