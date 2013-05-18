#!/usr/bin/env bash
dev_appserver --port 9999 .
appcfg.py upload_data --url=http://localhost:9999/_ah/remote_api --kind=Easter --filename=Easter.csv --config_file=bulkloader.yaml
appcfg.py upload_data --url=http://localhost:9999/_ah/remote_api --kind=Feast --filename=Feast.csv --config_file=bulkloader.yaml

