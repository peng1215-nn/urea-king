"""
结构化日志：每行一个 JSON，输出到标准输出（Railway 会自动收集）。
"""

import json
import logging
import sys
from datetime import datetime, timezone


_RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # logger.info("...", extra={...}) 传入的字段
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


_configured = False


def setup_logging(level="INFO"):
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers[:] = [handler]

    # LOG_LEVEL 写错时回退到 INFO，而不是让应用启动失败
    level = str(level or "INFO").upper()
    if level in logging.getLevelNamesMapping():
        root.setLevel(level)
    else:
        root.setLevel(logging.INFO)
        logging.getLogger("poker.settings").warning("invalid LOG_LEVEL %r, using INFO", level)

    # uvicorn 的访问日志与我们的请求日志重复，降低其级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    _configured = True
