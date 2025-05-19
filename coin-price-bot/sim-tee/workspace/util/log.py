import logging
import sys

logger = logging.getLogger("myproxy")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s %(message)s'))
logger.addHandler(handler)
