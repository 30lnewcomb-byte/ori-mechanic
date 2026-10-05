from .audit import AuditLog
from .models import Action, Approval
from .policy import classify_action

class MechanicCore:
    def __init__(self) -> None:
        self.audit = AuditLog()
        self.approvals: dict[str, Approval] = {}

    def evaluate(self, action: Action) -> dict:
        level = classify_action(action)
        self.audit.record("action_evaluated", action_id=action.id, autonomy=level.value)
        if level.value == "green":
            return {"decision": "execute", "autonomy": level.value}
        if level.value == "red":
            return {"decision": "deny", "autonomy": level.value}
        approval_id = f"approval-{action.id}"
        self.approvals[approval_id] = Approval(id=approval_id, action_id=action.id)
        self.audit.record("approval_requested", approval_id=approval_id, action_id=action.id)
        return {"decision": "await_approval", "autonomy": level.value, "approval_id": approval_id}

    def approve(self, approval_id: str) -> bool:
        approval = self.approvals.get(approval_id)
        if not approval or approval.status != "pending":
            return False
        approval.status = "approved"
        approval.decision = "APPROVE"
        self.audit.record("approval_granted", approval_id=approval_id)
        return True
