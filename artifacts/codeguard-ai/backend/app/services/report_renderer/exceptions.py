"""Exceptions for report renderer."""


class ReportRenderError(Exception):
    """Base exception."""


class DesignExtractionError(ReportRenderError):
    """Sample PDF could not be parsed for design tokens."""


class ContentExtractionError(ReportRenderError):
    """Project profile / sections could not be interpreted."""