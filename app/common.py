import httpx
from httpx import AsyncClient
from tenacity import retry, stop_after_attempt, wait_random_exponential
from datetime import datetime, timezone

LOGGER = None
DEFAULT_ATTRIBUTES = None


def configure_default_log_attributes(attributes: dict):
    global DEFAULT_ATTRIBUTES
    DEFAULT_ATTRIBUTES = attributes if isinstance(attributes, dict) else dict()
    return DEFAULT_ATTRIBUTES


def get_logger():
    import sys
    import os
    import json
    import logging.config
    global LOGGER
    if LOGGER is None:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        if os.getenv('LOGGING_CONFIG_PATH'):
            with open(os.getenv('LOGGER_CONFIG_PATH'), 'rt', encoding='utf-8') as f:
                config = json.load(f)
            logging.config.dictConfig(config=config)
        else:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        LOGGER = logging.getLogger()
    return LOGGER


def log_event(level: str, status: str, process_type: str, payload: dict):
    import json
    assert isinstance(payload, dict)
    assert status in {'success', 'anomalous', 'failure', 're-queued'}
    global DEFAULT_ATTRIBUTES
    attributes = DEFAULT_ATTRIBUTES if DEFAULT_ATTRIBUTES is not None else dict()
    level_mapping = dict(
        critical=50,
        error=40,
        warning=30,
        info=20,
        debug=10
    )
    log_message = {
        "process_type": process_type,
        "status": status,
        "payload": payload,
        **attributes
    }
    get_logger().log(level=level_mapping[level.lower()], msg=json.dumps(log_message))
    return log_message


def format_response_body(response):
    js = dict()
    try:
        js = response.json()
    except ValueError:
        js['content'] = response.text
    return js


def safe_json_request(method, url, stop=stop_after_attempt(3), reraise=True, filtered_response_keys=None,
                      raise_over=500, wait=wait_random_exponential(multiplier=.01, max=1), log_attributes=None,
                      **kwargs):
    if log_attributes is None:
        log_attributes = {k: v for k, v in kwargs.items() if k not in ['headers', 'files']}
    if filtered_response_keys is None:
        filtered_response_keys = []
    log_event(
        level='info', status='success', process_type='request_created', payload=dict(
            method=method,
            url=url,
            created_ts=datetime.now(tz=timezone.utc).timestamp(),
            **log_attributes
        )
    )
    return async_safe_json_request(
        method=method, url=url, stop=stop, reraise=reraise, wait=wait,
        filtered_response_keys=filtered_response_keys, raise_over=raise_over,
        log_attributes=log_attributes, **kwargs
    )


async def async_safe_json_request(method, url, log_attributes, filtered_response_keys, raise_over, reraise,
                                  stop, wait, **kwargs):
    import httpx
    @retry(stop=stop, reraise=reraise, wait=wait)
    async def make_async_request():
        resp = await AsyncClient().request(method=method, url=url, **kwargs)
        status, json_response = process_response(
            url=url, resp=resp, method=method, raise_over=raise_over,
            log_attributes=log_attributes, filtered_response_keys=filtered_response_keys
        )
        return status, json_response

    try:
        status_code, js = await make_async_request()
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        status_code, js = process_errors(
            url=url, exc=exc, method=method, log_attributes=log_attributes
        )
    return status_code, js


def process_response(method, url, resp, raise_over, filtered_response_keys, log_attributes):
    status = resp.status_code
    js = format_response_body(response=resp)
    level = 'info' if status < 400 else 'error'
    status_level = 'success' if status < raise_over else 'failure'
    log_event(
        level=level, status=status_level, process_type='request_completed', payload=dict(
            method=method,
            url=url,
            status=status,
            created_ts=datetime.now(tz=timezone.utc).timestamp(),
            response={k: v for k, v in js.items() if k not in filtered_response_keys},
            **log_attributes,
        )
    )
    if status >= raise_over:
        resp.raise_for_status()
    return status, js


def process_errors(exc, method, url, log_attributes):
    status_code, js = None, dict()
    if isinstance(exc, httpx.RequestError):
        log_event(
            level='error', status='failure', process_type='request_completed', payload=dict(
                method=method,
                url=url,
                status=status_code,
                created_ts=datetime.now(tz=timezone.utc).timestamp(),
                **log_attributes,
            )
        )
    elif isinstance(exc, httpx.HTTPStatusError):
        js = format_response_body(response=exc.response)
        status_code = exc.response.status_code
    return status_code, js
