from .registry import check_permission

def regulatory_guard(action, context):
    allowed, max_lev = check_permission(
        context["country"], context["product"]
    )

    if not allowed:
        return False, "REGULATION_BLOCK"

    if max_lev and context.get("leverage", 1) > max_lev:
        context["leverage"] = max_lev

    return True, context
