import xml.etree.ElementTree as ET

import httpx


class ZimbraClient:
    SOAP_URL = "https://mail.bsuedu.ru/service/soap"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(verify=False, timeout=15.0)

    @staticmethod
    def _soap_envelope(body: str, auth_token: str | None = None) -> str:
        context = f"<authToken>{auth_token}</authToken>" if auth_token else ""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Header>
    <context xmlns="urn:zimbra">{context}</context>
  </soap:Header>
  <soap:Body>{body}</soap:Body>
</soap:Envelope>"""

    async def authenticate(self, email: str, password: str) -> str | None:
        account = ET.Element("account", {"by": "name"})
        account.text = email
        password_element = ET.Element("password")
        password_element.text = password
        body = (
            '<AuthRequest xmlns="urn:zimbraAccount">'
            f"{ET.tostring(account, encoding='unicode')}"
            f"{ET.tostring(password_element, encoding='unicode')}"
            "</AuthRequest>"
        )
        xml = self._soap_envelope(body)
        response = await self.client.post(
            self.SOAP_URL,
            content=xml,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        )
        if response.is_error:
            return None
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return None
        token = root.find(".//{urn:zimbraAccount}authToken")
        if token is None or not token.text:
            return None
        self.client.cookies.set("ZM_AUTH_TOKEN", token.text)
        return token.text

    async def enable_protocols(self, auth_token: str) -> bool:
        xml = self._soap_envelope(
            '<ModifyPrefsRequest xmlns="urn:zimbraAccount">'
            '<pref name="zimbraPrefImapEnabled">TRUE</pref>'
            '<pref name="zimbraPrefPop3Enabled">TRUE</pref>'
            "</ModifyPrefsRequest>",
            auth_token,
        )
        response = await self.client.post(
            self.SOAP_URL,
            content=xml,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        )
        return response.is_success and "ModifyPrefsResponse" in response.text

    async def get_unread_messages(
        self, email: str, auth_token: str, limit: int = 5
    ) -> list[dict]:
        response = await self.client.get(
            f"https://mail.bsuedu.ru/home/{email}/inbox",
            params={"fmt": "json", "query": "is:unread", "limit": limit},
            cookies={"ZM_AUTH_TOKEN": auth_token},
        )
        response.raise_for_status()
        return response.json().get("m", [])

    async def close(self) -> None:
        await self.client.aclose()
