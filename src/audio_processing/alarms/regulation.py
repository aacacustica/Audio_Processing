from __future__ import annotations

from datetime import datetime


OCA_LIMITS = {
    "OCA_RESIDENTIAL": {
        "Ld": 65.0,
        "Le": 65.0,
        "Ln": 55.0,
    },
    "OCA_LEISURE": {
        "Ld": 73.0,
        "Le": 73.0,
        "Ln": 63.0,
    },
    "OCA_OFFICE": {
        "Ld": 70.0,
        "Le": 70.0,
        "Ln": 65.0,
    },
    "OCA_INDUSTRIAL": {
        "Ld": 75.0,
        "Le": 75.0,
        "Ln": 65.0,
    },
    "OCA_CULTURE": {
        "Ld": 60.0,
        "Le": 60.0,
        "Ln": 50.0,
    },
}


def evaluation_period(timestamp: datetime) -> str:

    hour = timestamp.hour

    if 7 <= hour < 19: return "Ld"
    if 19 <= hour < 23: return "Le"

    return "Ln"

def get_oca_limit(timestamp: datetime,*,oca_type:str) -> float:

    limits = OCA_LIMITS.get(oca_type)

    if limits is None: raise ValueError(f"Tipo OCA desconocido: {oca_type}")

    period = evaluation_period(timestamp)

    return limits[period]


