"""Fare calculation and secure transit-gate deployment helpers."""

from __future__ import annotations

from typing import Any, Iterable, cast

import paramiko
from cryptography.hazmat.primitives import hashes
from defusedxml import sax


DISTANCE_SLABS = ((2, 10), (5, 20), (12, 30), (21, 40), (32, 50))
MAX_FARE = 60
DAILY_CAP = 150
OFF_PEAK_DISCOUNT = 0.10
CONCESSIONS = {"student": 0.25, "senior": 0.50}
cards: dict[str, dict[str, object]] = {}


def _validate_distance(km: float) -> None:
    if not isinstance(km, (int, float)) or isinstance(km, bool) or km < 0:
        raise ValueError("distance must be a non-negative number")


def _validate_time(time_hhmm: str) -> None:
    try:
        hour, minute = (int(part) for part in time_hhmm.split(":", 1))
    except (AttributeError, ValueError) as error:
        raise ValueError("time must use HH:MM format") from error
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("time must use a valid 24-hour time")


def fare_for_distance(km: float) -> int:
    """Return the base fare for a non-negative distance."""
    _validate_distance(km)
    for limit, fare in DISTANCE_SLABS:
        if km < limit:
            return fare
    return MAX_FARE


def is_peak(time_hhmm: str) -> bool:
    """Return whether a valid time falls within a peak period."""
    _validate_time(time_hhmm)
    hour = int(time_hhmm.split(":", 1)[0])
    return 8 <= hour <= 10 or 17 <= hour <= 20


def journey_fare(
    km: float, time_hhmm: str, categories: Iterable[str] = ()
) -> float:
    """Calculate a journey fare after peak and concession adjustments."""
    fare = float(fare_for_distance(km))
    if not is_peak(time_hhmm):
        fare *= 1 - OFF_PEAK_DISCOUNT
    for category in categories:
        if category not in CONCESSIONS:
            raise ValueError(f"unknown concession category: {category}")
        fare *= 1 - CONCESSIONS[category]
    return round(fare, 2)


def daily_total(journeys: Iterable[tuple[float, str, Iterable[str]]]) -> float:
    """Return journey totals capped at the daily maximum."""
    total = sum(
        journey_fare(km, time, categories)
        for km, time, categories in journeys
    )
    return min(round(total, 2), DAILY_CAP)


def issue_card(card_id: str, balance: float = 0) -> None:
    """Create or replace a smart card after validating its balance."""
    if not card_id or not isinstance(card_id, str):
        raise ValueError("card_id must be a non-empty string")
    if (
        not isinstance(balance, (int, float))
        or isinstance(balance, bool)
        or balance < 0
    ):
        raise ValueError("balance must be a non-negative number")
    cards[card_id] = {"balance": round(float(balance), 2), "trips": []}


def _get_card(card_id: str) -> dict[str, object]:
    try:
        return cards[card_id]
    except KeyError as error:
        raise ValueError(f"unknown card: {card_id}") from error


def tap_out(
    card_id: str, km: float, time_hhmm: str, categories: Iterable[str] = ()
) -> float:
    """Charge a card for a journey and reject insufficient balances."""
    card = _get_card(card_id)
    fare = journey_fare(km, time_hhmm, categories)
    balance = float(card["balance"])
    if balance < fare:
        raise ValueError("insufficient card balance")
    card["balance"] = round(balance - fare, 2)
    trips = cast(list, card["trips"])
    trips.append((km, time_hhmm, fare))
    return card["balance"]


def top_up(card_id: str, amount: float) -> float:
    """Add a positive amount to an existing card."""
    card = _get_card(card_id)
    if (
        not isinstance(amount, (int, float))
        or isinstance(amount, bool)
        or amount <= 0
    ):
        raise ValueError("top-up amount must be positive")
    card["balance"] = round(float(card["balance"]) + amount, 2)
    return card["balance"]


def cheapest_route(routes: Iterable[float]) -> float:
    """Return the shortest route by its resulting base fare."""
    route_list = list(routes)
    if not route_list:
        raise ValueError("at least one route is required")
    return min(route_list, key=fare_for_distance)


def ticket_checksum(ticket_text: str) -> str:
    """Return a SHA-256 checksum for ticket integrity verification."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(ticket_text.encode("utf-8"))
    return digest.finalize().hex()


# SAX callback names are dictated by the parser API, so only this small
# adapter is exempt from the project's snake_case naming convention.
# pylint: disable=invalid-name
class StopHandler:
    """Collect stop names from a safely parsed XML document."""

    def __init__(self) -> None:
        self.stops: list[str] = []

    def processingInstruction(self, target: str, data: str) -> None:
        """Ignore processing instructions."""

    def setDocumentLocator(self, locator: Any) -> None:
        """Accept the parser's document locator."""

    def startDocument(self) -> None:
        """Mark the beginning of a document."""

    def endDocument(self) -> None:
        """Mark the end of a document."""

    def endElement(self, name: str) -> None:
        """Ignore closing tags."""

    def characters(self, content: str) -> None:
        """Ignore text outside stop attributes."""

    def ignorableWhitespace(self, whitespace: str) -> None:
        """Ignore whitespace between elements."""

    def skippedEntity(self, name: str) -> None:
        """Reject entity references that the safe parser does not resolve."""
        raise ValueError(f"unsupported entity: {name}")

    def startElement(self, name: str, attrs: Any) -> None:
        """Collect a stop element's name attribute."""
        if name == "stop":
            stop_name = attrs.get("name")
            if not stop_name:
                raise ValueError("stop elements require a name")
            self.stops.append(stop_name)


# pylint: enable=invalid-name


def load_stops(xml_text: str) -> list[str]:
    """Safely parse stop names, rejecting entity-expansion attacks."""
    handler = StopHandler()
    sax.parseString(xml_text.encode("utf-8"), handler)
    return handler.stops


def push_fares_to_gate(
    gate_host: str, fare_file: str, known_hosts_path: str | None = None
) -> None:
    """Upload a fare file using verified SSH host keys and a fixed command."""
    client = paramiko.SSHClient()
    if known_hosts_path:
        client.load_host_keys(known_hosts_path)
    else:
        client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(gate_host, username="depot")
    try:
        remote_file = "/var/lib/transit-fares.txt"
        with client.open_sftp() as sftp:
            sftp.put(fare_file, remote_file)
        transport = client.get_transport()
        if transport is None:
            raise RuntimeError("SSH transport was not established")
        channel = transport.open_session()
        channel.exec_command("install_fares /var/lib/transit-fares.txt")
        exit_status = channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(
                f"remote fare installation failed: {exit_status}"
            )
    finally:
        client.close()


def main() -> None:
    """Print a demonstration of the calculator's core features."""
    print("Fare for exactly 2 km:", fare_for_distance(2))
    print("Fare for exactly 32 km:", fare_for_distance(32))
    print("Is 20:45 peak?", is_peak("20:45"))
    print(
        "Student + senior card, 10 km off-peak:",
        journey_fare(10, "14:00", ["student", "senior"]),
    )
    day = [
        (30, "08:15", []),
        (30, "18:30", []),
        (40, "21:00", []),
        (35, "22:30", []),
    ]
    print("Daily total (cap 150):", daily_total(day))
    issue_card("C1", 60)
    print("Balance after a 30 km trip with Rs.60:", tap_out("C1", 30, "09:00"))
    issue_card("C2")
    print("Top up 0.1 then 0.2:", top_up("C2", 0.1), top_up("C2", 0.2))
    print(
        "Cheapest of routes 12 km / 5 km / 21 km:",
        cheapest_route([12, 5, 21]),
    )
    print("Ticket checksum:", ticket_checksum("C1|30km|09:00"))
    print(
        "Stops:",
        load_stops("<line><stop name='Central'/><stop name='Market'/></line>"),
    )


if __name__ == "__main__":
    main()
