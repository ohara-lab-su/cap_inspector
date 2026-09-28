from x_logger import XLogger

# logger = XLogger(log_level="info", logger_name="loop")
logger = XLogger(
    log_level="info",
    log_mode="rotate",
    log_name="save_name",
)

# logger.logger_name = "loop"
for i in range(10):
    logger.debug(f"{i}")

# logger.logger_name = "result"
logger.info(f"ループ回数、結果{i}")
