from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib import error, parse, request


class BoletinAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class BoletinAPIClient:
    base_url: str = "https://api-restboletinoficial.buenosaires.gob.ar"
    timeout: int = 30

    def obtener_boletin(self, parametro: str | int = 0, carga_datos: bool = True) -> dict[str, Any]:
        carga = "true" if carga_datos else "false"
        return self._get_json(f"/obtenerBoletin/{parse.quote(str(parametro))}/{carga}")

    def obtener_secciones_boletin(self, parametro: str | int) -> list[dict[str, Any]]:
        data = self._get_json(f"/obtenerSeccionesBoletin/{parse.quote(str(parametro))}")
        if not isinstance(data, list):
            raise BoletinAPIError("Expected a list from obtenerSeccionesBoletin")
        return data

    def obtener_normas_seccion(self, nro_boletin: int, superseccion_id: int) -> dict[str, Any]:
        return self._post_form_json(
            "/obtenerNormasSeccion",
            {"nro_boletin": str(nro_boletin), "superseccion_id": str(superseccion_id)},
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        return self._request_json("GET", path)

    def _post_form_json(self, path: str, data: dict[str, str]) -> dict[str, Any]:
        body = parse.urlencode(data).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._request_json("POST", path, body=body, headers=headers)

    def _request_json(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        req = request.Request(url, data=body, method=method, headers=headers or {})

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
                status = response.status
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise BoletinAPIError(f"HTTP {exc.code} from {url}: {detail}") from exc
        except error.URLError as exc:
            raise BoletinAPIError(f"Could not reach {url}: {exc.reason}") from exc

        if status < 200 or status >= 300:
            detail = raw.decode("utf-8", errors="replace")[:500]
            raise BoletinAPIError(f"HTTP {status} from {url}: {detail}")

        if "json" not in content_type.lower():
            detail = raw.decode("utf-8", errors="replace")[:500]
            raise BoletinAPIError(f"Expected JSON from {url}, got {content_type!r}: {detail}")

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            detail = raw.decode("utf-8", errors="replace")[:500]
            raise BoletinAPIError(f"Invalid JSON from {url}: {detail}") from exc

        if not isinstance(parsed, dict):
            raise BoletinAPIError(f"Expected JSON object from {url}")
        return parsed

