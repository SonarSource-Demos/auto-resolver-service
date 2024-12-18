#!/bin/bash
exec gunicorn server:app --config /apps/conf/gunicorn.py -k uvicorn.workers.UvicornWorker -w 4
