"""RF-NOT-02, RNF-02 y RNF-09 · Adaptador FCM con un doble de `messaging.send`, sin red."""

import logging

import pytest
from firebase_admin import exceptions, messaging

from app.modules.reminders.adapters.outbound.fcm_push_sender import CREDENTIALS_ENV, FcmPushSender
from app.modules.reminders.application.ports.outbound.push_sender import InvalidPushTokenError, PushDeliveryError


class FakeSend:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.messages: list[messaging.Message] = []

    def __call__(self, message: messaging.Message) -> str:
        self.messages.append(message)
        if self.error is not None:
            raise self.error
        return "projects/taia/messages/1"


def test_sends_the_message_to_the_token_rf_not_02():
    send = FakeSend()

    FcmPushSender(send).send("token-a", "Recuerda: Informe")

    [message] = send.messages
    assert message.token == "token-a"
    assert (message.notification.title, message.notification.body) == ("TAIA", "Recuerda: Informe")


@pytest.mark.parametrize("error", [
    messaging.UnregisteredError("no registrado"),
    messaging.SenderIdMismatchError("otro proyecto"),
    exceptions.InvalidArgumentError("token mal formado"),
])
def test_unregistered_or_invalid_token_is_reported_as_invalid_rf_not_02(error):
    sender = FcmPushSender(FakeSend(error))

    with pytest.raises(InvalidPushTokenError):
        sender.send("token-a", "Recuerda")


@pytest.mark.parametrize("error", [
    exceptions.UnavailableError("no disponible"),
    messaging.QuotaExceededError("cuota"),
    exceptions.InternalError("interno"),
])
def test_other_fcm_errors_are_retryable_rf_not_02(error):
    sender = FcmPushSender(FakeSend(error))

    with pytest.raises(PushDeliveryError):
        sender.send("token-a", "Recuerda")


def test_without_credentials_push_is_disabled_rnf_02_rnf_09(monkeypatch, caplog):
    monkeypatch.delenv(CREDENTIALS_ENV, raising=False)

    with caplog.at_level(logging.WARNING, logger="taia.reminders"):
        sender = FcmPushSender.from_env()

    assert sender is None
    assert [record.message for record in caplog.records] == ["fcm_disabled"]


@pytest.mark.parametrize("raw", ["no-es-json", "{}", '{"type": "service_account"}'])
def test_invalid_credentials_disable_push_without_logging_them_rnf_02_rnf_09(monkeypatch, caplog, raw):
    monkeypatch.setenv(CREDENTIALS_ENV, raw)

    with caplog.at_level(logging.WARNING, logger="taia.reminders"):
        sender = FcmPushSender.from_env()

    assert sender is None
    assert [record.message for record in caplog.records] == ["fcm_disabled"]
    assert raw not in caplog.text
    assert all(raw not in str(getattr(record, "fields", "")) for record in caplog.records)
