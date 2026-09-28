"""Dependencia HTTP compartida para autenticación Bearer."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.usuario.application.ports.inbound.identity import (
    IdentityService,
    get_identity_service,
)

_bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(_bearer_scheme),
]


def get_authenticated_user_id(request: Request, credentials: BearerCredentials) -> UUID:
    """Obtiene el usuario autenticado sin exponer detalles del contexto Usuario."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación requeridas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = _identity_service().authenticate(credentials.credentials)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    # Lo registra el log estructurado de la petición (RNF-05 permite el identificador).
    request.state.user_id = str(user_id)
    return user_id


def _identity_service() -> IdentityService:
    return get_identity_service()


CurrentUserId = Annotated[UUID, Depends(get_authenticated_user_id)]
