from .models import Action, Autonomy

AUTO_ACTIONS = {"retry_deployment", "restart_service", "health_check", "collect_logs", "clear_temporary_artifacts"}
APPROVAL_ACTIONS = {"rollback_deployment", "change_environment", "switch_provider", "modify_infrastructure"}
NEVER_ACTIONS = {"delete_infrastructure", "destroy_data", "reveal_credentials", "change_security_policy", "modify_authentication"}

def classify_action(action: Action) -> Autonomy:
    if action.action_type in NEVER_ACTIONS:
        return Autonomy.RED
    if action.action_type in APPROVAL_ACTIONS:
        return Autonomy.YELLOW
    if action.action_type in AUTO_ACTIONS:
        return Autonomy.GREEN
    return Autonomy.YELLOW

def allowed_to_execute(action: Action, approval_granted: bool = False) -> bool:
    level = classify_action(action)
    return level is Autonomy.GREEN or (level is Autonomy.YELLOW and approval_granted)
