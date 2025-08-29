#!/bin/bash
cd ../src
python -m unittest discover -s test -p 'test_*.py' -v
