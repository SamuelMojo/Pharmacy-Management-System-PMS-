"""Errors whose message is safe and useful to show to the person using the app.

The screens catch UserError and display its message. Anything else is treated as an
unexpected fault: it is logged and the person sees a generic message.
"""
from __future__ import annotations


class UserError(Exception):
    """Base class for problems the user can understand and fix."""


class ValidationError(UserError):
    """Input is not acceptable (empty name, weak password, bad date...)."""


class NotFoundError(UserError):
    """The record asked for does not exist."""


class ConflictError(UserError):
    """The action clashes with existing data (duplicate username...)."""
