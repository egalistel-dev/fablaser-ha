"""Constantes de l'intégration FabLaser."""

DOMAIN = "fablaser"

# États envoyés par le logiciel FabLaser (voir src/app-ha.js)
STATE_OFFLINE = "hors_ligne"
STATE_CONNECTED = "connecte"
STATE_RUNNING = "gravure"
STATE_PAUSED = "pause"
STATE_DONE = "termine"
STATE_ERROR = "erreur"
STATE_STOPPED = "arret"

STATES = [
    STATE_OFFLINE,
    STATE_CONNECTED,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_DONE,
    STATE_ERROR,
    STATE_STOPPED,
]
FINISHED_STATES = (STATE_DONE, STATE_ERROR, STATE_STOPPED)

EVENT_JOB_STARTED = f"{DOMAIN}_job_started"
EVENT_JOB_FINISHED = f"{DOMAIN}_job_finished"

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"
