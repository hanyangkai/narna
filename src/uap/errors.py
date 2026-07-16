"""UAP error taxonomy (UAP-Execution §10)."""


class UapError(Exception):
    """Base error for UAP SDK/runtime."""


class ValidationError(UapError):
    """Schema/input validation failed."""


class AuthorizationError(UapError):
    """Permission or policy denied."""


class ExecutionError(UapError):
    """Tool execution failed."""


class EvidenceError(UapError):
    """Required evidence missing or invalid."""


class UapRuntimeError(UapError):
    """Runtime state machine or internal failure."""
