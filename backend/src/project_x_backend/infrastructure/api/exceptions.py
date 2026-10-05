"""Stable, sanitized API error envelope."""

import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ResourceConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_detail = "The requested change conflicts with the current resource state."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", None)
    if response is None:
        logger.error(
            "Unhandled API exception",
            extra={"request_id": request_id, "exception_type": type(exc).__name__},
        )
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "details": None,
                    "request_id": request_id,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = getattr(exc, "default_code", "request_error")
    message = "The request could not be completed."
    details = response.data if response.status_code < 500 else None
    if response.status_code == 400:
        message = "Request validation failed."
    elif response.status_code == 401:
        message = "Authentication is required."
    elif response.status_code == 403:
        message = "The request is not permitted."
    elif response.status_code == 404:
        message = "The requested resource was not found."
    elif response.status_code == 409:
        message = "The request conflicts with the current resource state."
    response.data = {
        "error": {
            "code": str(code),
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }
    return response
