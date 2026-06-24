# Logger


Example on how to use the logger
```
import logging

logger = logging.getLogger(__name__)

logger.info("Loaded OCR backend '%s'.", engine)
logger.warning("Translation backend not installed.")
logger.error("Failed to load plugin '%s'.", plugin_name)
```
