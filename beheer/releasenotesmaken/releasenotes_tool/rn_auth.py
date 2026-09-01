"""
rn_auth.py - Inloggen via GitHub met de OAuth Device Flow (browser-login).

In plaats van een token te plakken, logt de gebruiker in de browser in met het
eigen GitHub-account. GitHub ondersteunt geen wachtwoord-login meer voor de API;
de Device Flow is de opvolger daarvan en geeft precies die ervaring:

  1. request_device_code() -> GitHub geeft een korte code + verificatie-URL.
  2. De gebruiker opent die URL, logt in en typt de code.
  3. poll_for_token() wacht tot de gebruiker akkoord geeft en levert dan een
     access-token op dat verder net als een PAT gebruikt wordt.

Eenmalige voorwaarde: een geregistreerde GitHub OAuth App met 'Device Flow'
aangezet. De Client ID daarvan is NIET geheim en mag in config.json bewaard
worden; er is geen client-secret nodig voor de Device Flow.
"""

import time

import requests


# Vaste Client ID van de GitHub OAuth App (met 'Device Flow' aan). Dit is
# GEEN geheim: OAuth client-id's zijn publieke identifiers en mogen in de code
# en in een repository staan. Hierdoor hoeft de gebruiker niets in te voeren.
DEFAULT_CLIENT_ID = "Ov23liOSBHq0H7pG5sd4"

DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

# 'repo' geeft lees/schrijf op repositories; nodig om (privé-)issues te lezen.
DEFAULT_SCOPE = "repo"


class AuthError(RuntimeError):
    """Fout tijdens het inloggen via de Device Flow."""


def request_device_code(client_id: str, scope: str = DEFAULT_SCOPE) -> dict:
    """Vraag een device- en gebruikerscode aan bij GitHub.

    Returns een dict met o.a. device_code, user_code, verification_uri,
    expires_in en interval.
    """
    try:
        resp = requests.post(
            DEVICE_CODE_URL,
            headers={"Accept": "application/json"},
            data={"client_id": client_id, "scope": scope},
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        raise AuthError(f"Netwerkfout bij verbinden met GitHub: {exc}") from exc

    if resp.status_code != 200:
        raise AuthError(
            f"GitHub gaf status {resp.status_code} terug: {resp.text[:200]}")

    data = resp.json()
    if data.get("error"):
        raise AuthError(_readable_error(data))
    if "device_code" not in data or "user_code" not in data:
        raise AuthError(f"Onverwacht antwoord van GitHub: {data}")
    return data


def poll_for_token(client_id: str, device_code: str, interval: int = 5,
                   expires_in: int = 900, on_wait=None,
                   should_cancel=None) -> str:
    """Wacht (pollend) tot de gebruiker akkoord geeft en geef het token terug.

    on_wait(bericht):   optionele callback voor voortgang.
    should_cancel():     optionele callback; geef True terug om te stoppen.
    """
    wait = max(int(interval or 5), 5)
    waited = 0
    while waited < expires_in:
        time.sleep(wait)
        waited += wait
        if should_cancel is not None and should_cancel():
            raise AuthError("Inloggen geannuleerd.")

        try:
            resp = requests.post(
                TOKEN_URL,
                headers={"Accept": "application/json"},
                data={"client_id": client_id, "device_code": device_code,
                      "grant_type": GRANT_TYPE},
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            raise AuthError(f"Netwerkfout tijdens inloggen: {exc}") from exc

        data = resp.json()
        token = data.get("access_token")
        if token:
            return token

        error = data.get("error")
        if error == "authorization_pending":
            if on_wait is not None:
                on_wait("Wachten op goedkeuring in de browser...")
            continue
        if error == "slow_down":
            wait += 5  # GitHub vraagt om rustiger te pollen
            continue
        if error == "expired_token":
            raise AuthError("De inlogcode is verlopen. Log opnieuw in.")
        if error == "access_denied":
            raise AuthError("Inloggen is in de browser geweigerd.")
        raise AuthError(_readable_error(data))

    raise AuthError("Time-out: te lang gewacht op goedkeuring in de browser.")


def _readable_error(data: dict) -> str:
    err = data.get("error", "onbekende_fout")
    desc = data.get("error_description")
    if err == "unauthorized_client" or "device flow" in (desc or "").lower():
        return ("De OAuth App heeft 'Device Flow' niet aanstaan, of de "
                "Client ID klopt niet. Zet in de App-instellingen "
                "'Enable Device Flow' aan en controleer de Client ID.")
    return f"Inloggen mislukt: {desc or err}"
