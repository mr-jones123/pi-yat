"""Entry point for the CryptoGuard server."""

import uvicorn

from cryptoguard.config import Settings


def main():
    settings = Settings()
    uvicorn.run(
        "cryptoguard.api:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
