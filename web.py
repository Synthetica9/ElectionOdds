#!/usr/bin/env nix-shell
#!nix-shell -i python3

from flask import Flask, request, send_file, after_this_request
from itertools import chain
from uuid import uuid4
import os

import main
from tools import cache

app = Flask(__name__)


@app.route('/')
def send_index():
    main.main()
    return send_file('out.svg')


if __name__ == "__main__":
    app.run(threaded=False)
