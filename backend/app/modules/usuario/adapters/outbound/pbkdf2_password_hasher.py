"""Adaptador de hashing de contraseñas usando PBKDF2 de la biblioteca estándar."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from backend.app.modules.usuario.application.ports.outbound.password_hasher import PasswordHasher


class Pbkdf2PasswordHasher(PasswordHasher):
    """Protege contraseñas sin acoplar el dominio a una biblioteca concreta."""

    iterations = 310_000

    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.iterations)
        return "pbkdf2_sha256${}${}${}".format(
            self.iterations,
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(derived).decode(),
        )

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            salt = base64.urlsafe_b64decode(salt_b64.encode())
            expected = base64.urlsafe_b64decode(digest_b64.encode())
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, int(iterations)
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False
