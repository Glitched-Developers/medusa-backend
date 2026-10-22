from enum import Enum


class NotificationType(str, Enum):
    MAIL = "zimbra_mail"
    SCHEDULE_CHANGE = "schedule_change"
