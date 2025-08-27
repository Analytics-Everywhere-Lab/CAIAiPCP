#!/bin/bash
docker exec \
  -it \
  vector_db psql \
  -P expanded=auto \
  -U aip_user -d aip_db
