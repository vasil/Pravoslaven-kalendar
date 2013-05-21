#!/usr/bin/env bash
/opt/google_appengine/dev_appserver.py --datastore_path ../datastore.sqlite3 --port 9999 .. &
/opt/google_appengine/appcfg.py upload_data --url=http://localhost:9999/_ah/remote_api --kind=Easter --filename=Easter.csv --config_file=bulkloader.yaml
/opt/google_appengine/appcfg.py upload_data --url=http://localhost:9999/_ah/remote_api --kind=Feast --filename=Feast.csv --config_file=bulkloader.yaml

