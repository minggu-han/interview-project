"""统一日志配置。

在 app.main 导入时调用 setup_logging() 完成全局配置，
其余模块用 logging.getLogger(__name__) 获取 logger。
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    # 强制 stdout 用 UTF-8，避免 Windows GBK 控制台中文日志乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        # 某些环境下 stdout 不支持 reconfigure，忽略即可
        pass

    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt))

    root = logging.getLogger()
    root.setLevel(level)
    # 避免 --reload 重复 add handler
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    else:
        for h in root.handlers:
            h.setFormatter(logging.Formatter(fmt, datefmt))

    # 应用自身命名空间统一 INFO
    logging.getLogger("app").setLevel(level)
