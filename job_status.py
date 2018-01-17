#!/bin/env python

# Slack integration to our build,CI/CD pipelines

import re
import os
import json
import time
import requests
from pprint import pprint
from flask import Flask, jsonify, request

def build_fields(current_job, status, full_url):
    fields = [
        {
            "title": "current job",
            "value": current_job,
            "short": True
        },
        {
            "title": "status",
            "value": status,
            "short": True
        },
        {
            "title": "job url",
            "value": full_url,
            "short": False
        }
    ]
    return fields

def build_payload(repo, color, fields, started_by):
    data = {
        "text": "GIT: %s" % repo,
        "attachments": [
            {
                "color": color,
                "fields": fields,
                "footer": "started by: %s" % started_by,
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": int(time.time())
            }
        ]
    }
    return data

slack_webhook = 'slack webhook URL'
logdir = '/home/y/logs/slack_server/'
logfile = 'server.log'

if not os.path.exists(logdir):
    os.makedirs(logdir)

logger = logdir + logfile

app = Flask(__name__)

@app.route('/sd_build', methods = ['POST'])
def sd_status():

    if request.method == 'POST':
        content = json.loads(request.data)

        build_num   = content['build']['number']
        phase       = content['build']['phase']
        started_by  = content['build']['parameters']['_started_by']
        full_url    = content['build']['full_url']
        repo        = content['build']['scm']['url']
        job         = content['build']['url']
        current_job = re.match("^job\/\d+-v3-(.+)\/\d+", job).group(1)

        if phase == 'STARTED':
            status  = phase
            color   = '#070707'
            fields  = build_fields(current_job, status, full_url)
            payload = build_payload(repo, color, fields, started_by)
            requests.post(post_url, data=json.dumps(payload))

        elif phase == 'FINALIZED':
            status = content['build']['status']
            if status == 'SUCCESS':
                color = 'good'
            elif status == 'ABORTED':
                color = 'warning'
            elif status == 'FAILURE':
                color = 'danger'

            fields  = build_fields(current_job, status, full_url)
            payload = build_payload(repo, color, fields, started_by)
            requests.post(slack_webhook, data=json.dumps(payload))

        return 'OK'


if __name__ == '__main__':
    import logging

    logging.basicConfig(filename=logger, level=logging.DEBUG)
    app.run(host = '0.0.0.0', port=9888)
