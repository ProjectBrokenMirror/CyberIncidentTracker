from app.connectors.base import SourceConnector
from app.connectors.databreach_net import DataBreachesConnector
from app.connectors.hhs_ocr import HhsOcrConnector
from app.connectors.sec_8k import Sec8KConnector


def wave1_connectors() -> list[SourceConnector]:
    # Additional Wave 1 connectors can be added here as implemented.
    return [DataBreachesConnector(), Sec8KConnector(), HhsOcrConnector()]
