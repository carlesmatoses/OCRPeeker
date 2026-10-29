class PluginUnavailable(RuntimeError):
    """A named plugin is not installed."""


class SegmenterUnavailable(PluginUnavailable):
    """No segmenter plugin is registered under the requested name."""


class OCRBackendUnavailable(PluginUnavailable):
    """No OCR plugin is registered under the requested name."""
