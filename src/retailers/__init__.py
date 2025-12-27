from . import intermarche
from . import carrefour

RETAILERS = {
    "intermarche": intermarche,
     "carrefour": carrefour,
}

def get_retailer(name: str):
    return RETAILERS.get(name)

__all__ = [
    "RETAILERS",
    "get_retailer",
]
