import os

REQUIRED = (
    "MESSENGER_TOKEN_AI_A",
    "MESSENGER_TOKEN_AI_B",
    "MESSENGER_AI_ID_A",
    "MESSENGER_AI_ID_B",
)

def validate_staging_environment(env=None):
    values = os.environ if env is None else env
    errors = []
    for name in REQUIRED:
        if not values.get(name):
            errors.append("missing:" + name)

    db_path = values.get("MESSENGER_DB_PATH", "server/data/messenger.sqlite")
    if not db_path or db_path != db_path.strip():
        errors.append("invalid:MESSENGER_DB_PATH")

    try:
        timeout = int(values.get("MESSENGER_REQUEST_TIMEOUT_SECONDS", "10"))
        if not 1 <= timeout <= 120:
            errors.append("invalid:MESSENGER_REQUEST_TIMEOUT_SECONDS")
    except ValueError:
        errors.append("invalid:MESSENGER_REQUEST_TIMEOUT_SECONDS")

    try:
        retries = int(values.get("MESSENGER_RETRY_LIMIT", "2"))
        if not 0 <= retries <= 5:
            errors.append("invalid:MESSENGER_RETRY_LIMIT")
    except ValueError:
        errors.append("invalid:MESSENGER_RETRY_LIMIT")

    return tuple(errors)

def assert_staging_environment(env=None):
    errors = validate_staging_environment(env)
    if errors:
        raise RuntimeError("staging_configuration_invalid:" + ",".join(errors))
    return True
