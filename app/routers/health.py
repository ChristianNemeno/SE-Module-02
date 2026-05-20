from fastapi import APIRouter


class HealthController:
    """Handles GET /health — liveness probe, no auth, no business logic."""

    def __init__(self) -> None:
        self.router = APIRouter(tags=["health"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def health(self) -> dict[str, str]:
        """Returns {"status": "ok"} — used by Docker HEALTHCHECK and Nginx upstream checks."""
        return {"status": "ok"}
