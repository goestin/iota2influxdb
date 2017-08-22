#!/usr/bin/env python
from iota import StrictIota
from influxdb import InfluxDBClient
import pprint
import json
import argparse
import datetime
import time

pp = pprint.PrettyPrinter()

parser = argparse.ArgumentParser()
parser.add_argument('--uri', nargs='+', default=["http://localhost:14265"], help="uri for the iota api endpoint. Define multiple entries by seperating them with spaces. Default value: \"http://localhost:14625\"")
parser.add_argument('--dbhost', default="localhost", help="hostname for the influxdb http endpoint. May also be a IP address. Default value: \"localhost\"")
parser.add_argument('--dbport', default="8086", help="port of the influxdb http endpoint. Default value: \"8086\"")
parser.add_argument('--dbuser', default="", help="User for connection to influxdb. Default value: \"\"")
parser.add_argument('--dbpassword', default="", help="Password for influxdb user. Default value: \"\"")
parser.add_argument('--dbname', default="iota", help="Name of the database to use. Default value: \"iota\"")
args = parser.parse_args()

influxclient = InfluxDBClient(args.dbhost, args.dbport, args.dbuser, args.dbpassword, args.dbname)
influxclient.create_database(args.dbname)

def getNodeInfo(uris):
	json_data = []
	for uri in uris:
		api=StrictIota(uri)
		try:
			print('>>> Requesting getNodeInfo from: \"%s\": ' % uri),
			nodeinfo=api.get_node_info()
			skip=False
		except Exception,error:
			print("ERROR: %s" % error)
			skip=True

		print("SUCCESS")
		if skip == False:
			nodeinfo['latestMilestone']=nodeinfo['latestMilestone'].as_json_compatible()
			nodeinfo['latestSolidSubtangleMilestone']=nodeinfo['latestSolidSubtangleMilestone'].as_json_compatible()

			fields = {
				'duration': nodeinfo['duration'],
				'jreAvailableProcessors': nodeinfo['jreAvailableProcessors'],
				'jreFreeMemory': nodeinfo['jreFreeMemory'],
				'jreMaxMemory': nodeinfo['jreMaxMemory'],
				'jreTotalMemory': nodeinfo['jreTotalMemory'],
				'latestMilestoneIndex': nodeinfo['latestMilestoneIndex'],
				'latestSolidSubtangleMilestoneIndex': nodeinfo['latestSolidSubtangleMilestoneIndex'],
				'neighbors': nodeinfo['neighbors'],
				'packetsQueueSize': nodeinfo['packetsQueueSize'],
				'tips': nodeinfo['tips'],
				'transactionsToRequest': nodeinfo['transactionsToRequest']
			}

			tags = {
				'node': uri.split('//')[1].split(':')[0],
				'appName': nodeinfo['appName'],
				'appVersion': nodeinfo['appVersion'],
				'jreVersion': nodeinfo['jreVersion']
			}
			json_data.append(createInfluxMeasurement("node_info", fields=fields, tags=tags))
	return(json_data)

def getNeighbors(uris):
	json_data = []
	for uri in uris:
		api=StrictIota(uri)
		try:
			print('>>> Requesting getNeighbors from: \"%s\": ' % uri),
			neighbors=api.get_neighbors()
			skip=False
		except Exception,error:
			print("ERROR: %s" % error)
			skip=True

		print("SUCCES")
		if skip == False:
			for neighbor in neighbors['neighbors']:
				fields = {
					'numberOfAllTransactions': neighbor['numberOfAllTransactions'],
					'numberOfInvalidTransactions': neighbor['numberOfInvalidTransactions'],
					'numberOfNewTransactions': neighbor['numberOfNewTransactions'],
					'numberOfRandomTransactionRequests': neighbor['numberOfRandomTransactionRequests'],
					'numberOfSentTransactions': neighbor['numberOfSentTransactions']
				}

				tags = {
					'source': uri.split('//')[1].split(':')[0],
					'address': neighbor['address'],
					'connectionType': neighbor['connectionType']
				}
				json_data.append(createInfluxMeasurement("neighbors", fields=fields, tags=tags))
	return(json_data)

def createInfluxMeasurement(name, fields={}, tags={}):
	json_body = {
			"measurement": name,
			"tags": tags,
			"time": datetime.datetime.utcnow().isoformat(),
			"fields": fields
		}
	return(json_body)
		
def writeInfluxMeasurement(measurement):
	influxclient.write_points(measurement)
	
while True:
	measurement = getNodeInfo(args.uri)
#	pp.pprint(measurement)
	writeInfluxMeasurement(measurement)
	measurement = getNeighbors(args.uri)
#	pp.pprint(measurement)
	writeInfluxMeasurement(measurement)
	print('III sleeping for 10 seconds...')
	time.sleep(10)


