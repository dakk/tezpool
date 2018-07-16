#!/usr/bin/python3

#http://doc.tzalpha.net/api/rpc_proposal.html?highlight=june
#http://doc.tzalpha.net/api/rpc.html#usage

import json
import requests
import time
import argparse
import sys

# Constants
PRESERVED_CYCLES = 5

# Force python3
if sys.version_info[0] < 3:
	print ('python2 not supported, please use python3')
	sys.exit (0)

# Parse command line args
parser = argparse.ArgumentParser(description='Tezos delegate redistribution script')
parser.add_argument('-c', metavar='config.json', dest='cfile', action='store',
				   default='config.json',
				   help='set a config file (default: config.json)')

args = parser.parse_args ()

# Load the config file
try:
	conf = json.load (open (args.cfile, 'r'))
except:
	print ('Unable to load config file.')
	sys.exit ()

def formatBalance (bal):
	return str (int (bal) / 1000000)

def getBlockHashByIndex (idx):
	head_level = requests.get (conf['host'] + '/chains/main/blocks/head/header').json()['level']
	return requests.get (conf['host'] + '/chains/main/blocks/head~' + str (head_level - idx) + '/header').json()['hash']

def getCycleSnapshot (cycle):
	print ('Cycle', cycle)

	# Get the snapshot block for every cycle /chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/7
	snapshot_block_offset = requests.get (conf['host'] + '/chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/' + str(cycle)).json()[0]

	# Then multiply the result with 256 and sum the cycle index, we get the block of the snapshot
	snapshot_block_index = ((cycle-PRESERVED_CYCLES-2)*4096)+((snapshot_block_offset+1)*256)
	#print ('\t', snapshot_block_index, snapshot_block_offset)

	# Get the delegate information for the given snapshot
	block_hash = getBlockHashByIndex (snapshot_block_index)
	delegate_info = requests.get (conf['host'] + "/chains/main/blocks/" + block_hash + "/context/delegates/" + conf['pkh']).json()

	delegated = []
	print ('\t', 'Staking Balance:', formatBalance (delegate_info['staking_balance']))
	#print ('\t', 'Delegate Balance:', formatBalance (delegate_info['balance']))

	# Get the delegated balance of each contract
	for x in delegate_info['delegated_contracts']:
		contract_info = requests.get (conf['host'] + "/chains/main/blocks/" + block_hash + "/context/contracts/" + x).json()

		contract_info2 = {
			"balance": contract_info['balance'],
			"manager": contract_info['manager'],
			"contract": x,
			"name": conf['names'][contract_info['manager']] if (contract_info['manager'] in conf['names']) else None,
			"percentage": 100. * int (contract_info['balance']) / int (delegate_info['staking_balance'])
		}
		delegated.append(contract_info2)

	# Append the delegate as contractor
	delegated.append({
		"balance": delegate_info['balance'],
		"manager": conf['pkh'],
		"contract": None,
		"name": "dakk",
		"percentage": 100. * int (delegate_info['balance']) / int (delegate_info['staking_balance'])
	})

	for x in delegated:
		print ('\t', x['manager'], x['name'], '->', formatBalance (x['balance']), '(' + str(x['percentage']) + '%)')

	return {
		"cycle": cycle,
		"staking_balance": delegate_info['staking_balance'],
		"delegated": delegated
	}



	"""
	{
		'balance': '25004950000', 'grace_period': 11, 'frozen_balance': '0', 
		'delegated_contracts': ['KT1UuNjaWzA9YseRBmYn6XceUrXoQE4ZHJ8X', 'KT1TpQqirScT2o4eLrcWb2qXibasVUdJ4F8f', 'KT1KQhhaJdjysa2ihdNeXCsCFsekQM4PoDzA', 
			'KT1JLRENDnZG4mtH6exB7D2t9ttXsoveEt5e', 'KT1HtcckeAhQoq2L9TTwreiZYcjnMANwnErh', 'KT1D6auSy8nE9bxjikuxxYpUkjXJus3vJ7hX', 'KT18ctzhc7VTtiZpohPEowFQvTmAJZGuMo2N'], 
		'deactivated': False, 'delegated_balance': '71914325100', 'staking_balance': '96919275100', 'frozen_balance_by_cycle': []}

	a = requests.get (conf['host'] + "/chains/main/blocks/" + snapshot_block_hash + "/context/delegates/" + conf['pkh']).json()
	print ('\t', a)
	a = requests.get (conf['host'] + "/chains/main/blocks/" + getBlockHashByIndex (snapshot_block_index - 1) + "/context/delegates/" + conf['pkh']).json()
	print ('\t', a)
	a = requests.get (conf['host'] + "/chains/main/blocks/" + getBlockHashByIndex (snapshot_block_index + 1) + "/context/delegates/" + conf['pkh']).json()
	print ('\t', a)
	
	>>> (2 * 16 + 42 * 2)  / (2 * 24 + 20)
	1.7058823529411764
	>>> (2 * 16 + 42 * 2)  / (2 * 24 + 20) * 24
	40.94117647058823
	"""

for x in range(7, 13):
	getCycleSnapshot(x)