#!/bin/sh

while true; do
	cur_date=`date "+%Y-%m-%d %H:%M"`
	cur_ts=`date -d "$cur_date" +%s`
	sample_ts=$((cur_ts - 60))
	val=`python ./get_connectnum.py`
	
	curl -X POST --connect-timeout 5 --max-time 5 -d '[{"metric": "dns.query.rndc", "endpoint": "lb4test", "timestamp": '$sample_ts', "step": 60,"value": '$val', "counterType": "GAUGE", "tags": "test"}]' http://127.0.0.1:1988/v1/push
	sleep 60s
done
