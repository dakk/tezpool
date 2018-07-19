#!/usr/bin/python3

#http://doc.tzalpha.net/api/rpc_proposal.html?highlight=june
#http://doc.tzalpha.net/api/rpc.html#usage

import json
import requests
import time
import argparse
import math
import sys

# Constants
PRESERVED_CYCLES = 5
BLOCK_REWARD = 16 * 1000000.
ENDORSMENT_REWARD = 2 * 1000000.
BLOCKS_PER_CYCLE = 4096


# Force python3
if sys.version_info[0] < 3:
	print ('python2 not supported, please use python3')
	sys.exit (0)


# Parse command line args
parser = argparse.ArgumentParser(description='Tezos delegate redistribution script')
parser.add_argument('-c', '--config', metavar='config.json', dest='cfile', action='store',
				   default='config.json',
				   help='set a config file (default: config.json)')
parser.add_argument('action', metavar='action', action='store',
				   type=str, choices=['estimate', 'percentage', 'updatependings', 'paypendings'],
				   help='action to perform (estimate, percentage, updatependings, paypendings)')
parser.add_argument('-cc', '--cycle', metavar='cycle', action='store', default=None,
				   type=int, help='cycle number (default is the current cycle)')

args = parser.parse_args ()


# Load the config file
try:
	conf = json.load (open (args.cfile, 'r'))
except:
	print ('Unable to load config file.')
	sys.exit ()


def formatBalance (bal):
	return str (int (bal) / 1000000)


def getCurrentCycle ():
	return math.floor (requests.get (conf['host'] + '/chains/main/blocks/head/header').json()['level'] / BLOCKS_PER_CYCLE)


def getBlockHashByIndex (idx):
	head_level = requests.get (conf['host'] + '/chains/main/blocks/head/header').json()['level']
	return requests.get (conf['host'] + '/chains/main/blocks/head~' + str (head_level - idx) + '/header').json()['hash']

def getFrozenBalance ():
	return requests.get (conf['host'] + '/chains/main/blocks/head/context/delegates/' + conf['pkh'] + '/frozen_balance_by_cycle').json()

def getCycleSnapshot (cycle):
	# Get the snapshot block for every cycle /chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/7
	snapshot_block_offset = requests.get (conf['host'] + '/chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/' + str(cycle)).json()[0]

	# Then multiply the result with 256 and sum the cycle index, we get the block of the snapshot
	snapshot_block_index = ((cycle-PRESERVED_CYCLES-2)*4096)+((snapshot_block_offset+1)*256)
	#print ('\t', snapshot_block_index, snapshot_block_offset)

	# Get the delegate information for the given snapshot
	block_hash = getBlockHashByIndex (snapshot_block_index)
	delegate_info = requests.get (conf['host'] + "/chains/main/blocks/" + block_hash + "/context/delegates/" + conf['pkh']).json()

	delegated = []

	# Get the delegated balance of each contract
	for x in delegate_info['delegated_contracts']:
		contract_info = requests.get (conf['host'] + "/chains/main/blocks/" + block_hash + "/context/contracts/" + x).json()

		contract_info2 = {
			"balance": contract_info['balance'],
			"manager": contract_info['manager'],
			"contract": x,
			"name": conf['deleguees'][contract_info['manager']] if (contract_info['manager'] in conf['deleguees']) else None,
			"percentage": int (100. * int (contract_info['balance']) / int (delegate_info['staking_balance']))
		}
		delegated.append(contract_info2)

	# Append the delegate as contractor
	delegated.append({
		"balance": delegate_info['balance'],
		"manager": conf['pkh'],
		"contract": None,
		"name": conf['name'],
		"percentage": int (100. * int (delegate_info['balance']) / int (delegate_info['staking_balance']))
	})


	return {
		"cycle": cycle,
		"staking_balance": delegate_info['staking_balance'],
		"delegated": delegated
	}



def getBakingAndEndorsmentRights (cycle):
	bak = requests.get (conf['host'] + "/chains/main/blocks/head/helpers/baking_rights?delegate=" + conf['pkh'] + '&cycle=' + str(cycle)).json()
	endors = requests.get (conf['host'] + "/chains/main/blocks/head/helpers/endorsing_rights?delegate=" + conf['pkh'] + '&cycle=' + str(cycle)).json()

	b = list(filter(lambda x: x['priority'] == 1, bak))
	e = endors
	
	return {
		'blocks': b,
		'endorsment': e,
		'estimated_reward': len(b) * BLOCK_REWARD + len(e) * ENDORSMENT_REWARD
	}

def getRewardForPastCycle (cycle):
	pass



# Get the current cycle if None is provided
if args.cycle == None:
	args.cycle = getCurrentCycle()

if args.action == 'estimate':
	print ('Cycle:', args.cycle)
	snap = getCycleSnapshot(args.cycle)
	brights = getBakingAndEndorsmentRights(args.cycle)

	print ('Staking Balance:', formatBalance (snap['staking_balance']))
	reward = brights['estimated_reward'] - brights['estimated_reward'] * (100 - conf['percentage']) / 100.

	print ('Total estimated reward:', formatBalance (brights['estimated_reward']), 'XTZ')
	print ('Reward without fee (' + str (conf['percentage']) + '%):', formatBalance (reward), 'XTZ')
	print()
	for x in snap['delegated']:
		urew = formatBalance (reward * x['percentage'] / 100.)
		print (x['manager'], x['name'], '->', urew, 'XTZ (' + str(x['percentage']) + '%)')


elif args.action == 'percentage':
	print ('Cycle:', args.cycle)
	snap = getCycleSnapshot(args.cycle)

	print ('Staking Balance:', formatBalance (snap['staking_balance']))

	for x in snap['delegated']:
		print (x['manager'], x['name'], '->', formatBalance (x['balance']), 'XTZ (' + str(x['percentage']) + '%)')


elif args.action == 'updatependings':
	pass

elif args.action == 'paypendings':
	pass