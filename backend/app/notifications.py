from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain import NotificationChannel


@dataclass(frozen=True)
class DeliveryResult:
    provider_message_id: str
    accepted_at: str


class NotificationProvider(Protocol):
    channel: NotificationChannel

    def send(self, destination: str, body: str, idempotency_key: str) -> DeliveryResult:
        """Send a notification and return the provider receipt."""


class LocalNotificationProvider:
    def __init__(self, channel: NotificationChannel):
        self.channel = channel

    def send(self, destination: str, body: str, idempotency_key: str) -> DeliveryResult:
        del destination, body
        return DeliveryResult(
            provider_message_id=f"local-{self.channel.value.lower()}-{idempotency_key[:12]}",
            accepted_at="",
        )


PROVIDERS: dict[NotificationChannel, NotificationProvider] = {
    channel: LocalNotificationProvider(channel) for channel in NotificationChannel
}
