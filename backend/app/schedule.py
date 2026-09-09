"""Maintenance schedule evaluation and specification logic."""

from enum import StrEnum
from datetime import date as date_type
from typing import Any, Optional, List, Dict


class ScheduleRuleType(StrEnum):
    DATE_ONLY = "DATE_ONLY"
    ODOMETER_ONLY = "ODOMETER_ONLY"
    WHICHEVER_COMES_FIRST = "WHICHEVER_COMES_FIRST"
    WHICHEVER_COMES_LAST = "WHICHEVER_COMES_LAST"


class ScheduleStatus(StrEnum):
    PLANNED = "PLANNED"
    DUE = "DUE"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


def schedule_specifications(service: Any) -> List[Dict[str, Any]]:
    """Extract maintenance schedule specifications from a service record.
    
    Returns a list of dicts with: maintenance_type, due_date, due_odometer, rule_type, source_service_item_id
    """
    specifications = []
    for item in service.items:
        due_date = item.next_due_date
        due_odometer = item.next_due_odometer
        if due_date is None and due_odometer is None:
            continue
        
        rule_type = item.rule_type
        if rule_type is None:
            rule_type = (
                ScheduleRuleType.WHICHEVER_COMES_FIRST.value
                if due_date is not None and due_odometer is not None
                else ScheduleRuleType.DATE_ONLY.value
                if due_date is not None
                else ScheduleRuleType.ODOMETER_ONLY.value
            )
        try:
            rule_type = ScheduleRuleType(rule_type).value
        except ValueError:
            raise ValueError("Unknown maintenance schedule rule.")
        
        if rule_type in {ScheduleRuleType.DATE_ONLY.value, ScheduleRuleType.WHICHEVER_COMES_LAST.value} and due_date is None:
            raise ValueError("This rule requires a due date.")
        if rule_type in {ScheduleRuleType.ODOMETER_ONLY.value, ScheduleRuleType.WHICHEVER_COMES_LAST.value} and due_odometer is None:
            raise ValueError("This rule requires a due odometer.")
        if rule_type == ScheduleRuleType.WHICHEVER_COMES_FIRST.value and (due_date is None or due_odometer is None):
            raise ValueError("This rule requires a due date and odometer.")
        
        specifications.append(
            {
                "maintenance_type": item.service_category or service.service_type or "SERVICE",
                "due_date": due_date,
                "due_odometer": due_odometer,
                "rule_type": rule_type,
                "source_service_item_id": item.id,
            }
        )
    return specifications


def evaluate_schedule(schedule: Dict[str, Any], evaluated_at: Any, odometer: int) -> str:
    """Evaluate a maintenance schedule's current status.
    
    Returns one of: PLANNED, DUE, OVERDUE
    """
    from datetime import datetime
    
    current_date = evaluated_at.astimezone(datetime.timezone.utc).date()
    due_date = date_type.fromisoformat(schedule["due_date"]) if schedule.get("due_date") else None
    due_odometer = schedule.get("due_odometer")
    
    date_due = due_date is not None and current_date >= due_date
    odometer_due = due_odometer is not None and odometer >= due_odometer
    date_overdue = due_date is not None and current_date > due_date
    odometer_overdue = due_odometer is not None and odometer > due_odometer
    
    rule_type = schedule["rule_type"]
    if rule_type == ScheduleRuleType.DATE_ONLY.value:
        due, overdue = date_due, date_overdue
    elif rule_type == ScheduleRuleType.ODOMETER_ONLY.value:
        due, overdue = odometer_due, odometer_overdue
    elif rule_type == ScheduleRuleType.WHICHEVER_COMES_FIRST.value:
        due, overdue = date_due or odometer_due, date_overdue or odometer_overdue
    else:  # WHICHEVER_COMES_LAST
        due, overdue = date_due and odometer_due, date_overdue and odometer_overdue
    
    if overdue:
        return ScheduleStatus.OVERDUE.value
    elif due:
        return ScheduleStatus.DUE.value
    else:
        return ScheduleStatus.PLANNED.value


def schedule_history_entry(previous_status: Optional[str], new_status: str, 
                          actor_user_id: str, reason: str) -> Dict[str, Any]:
    """Create a schedule history entry for audit trail."""
    from datetime import datetime as dt
    return {
        "previous_status": previous_status,
        "new_status": new_status,
        "actor_user_id": actor_user_id,
        "occurred_at": dt.now(dt.timezone.utc).isoformat(),
        "reason": reason,
    }
