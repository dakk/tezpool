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
				   type=str, choices=['updatependings', 'paypendings', 'updatedocs'],
				   help='action to perform (updatependings, paypendings, updatedocs)')

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

def getFrozenBalance (cycle = None):
	if cycle == None:
		block = 'head'
	else:
		ccycle = getCurrentCycle ()
		clevel = requests.get (conf['host'] + '/chains/main/blocks/head/helpers/levels_in_current_cycle?offset=-'+str(ccycle - cycle)).json()
		block = getBlockHashByIndex (clevel['last'])

	r = requests.get (conf['host'] + '/chains/main/blocks/' + block + '/context/delegates/' + conf['pkh'] + '/frozen_balance_by_cycle').json()
	if cycle != None:
		return list (filter (lambda y: y['cycle'] == cycle, r))[0]
	else:
		return r


def getCycleSnapshot (cycle):
	#snapshot_block_offset = requests.get (conf['host'] + '/chains/main/blocks/head/context/raw/json/rolls/owner/snapshot/' + str(cycle)).json()[0]	

	# Then multiply the result with 256 and sum the cycle index, we get the block of the snapshot
	#snapshot_block_index = ((cycle-PRESERVED_CYCLES-2)*4096)+((snapshot_block_offset+1)*256)

	snapshot_block_index = ((cycle-PRESERVED_CYCLES-2)*4096)+4095
	
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
			"address": x,
			"alias": conf['deleguees'][x] if (x in conf['deleguees']) else None,
			"percentage": (int (10000. * 100. * float (contract_info['balance']) / float (delegate_info['staking_balance']))) / 10000.
		}
		delegated.append(contract_info2)

	# Append the delegate as contractor
	delegated.append({
		"balance": delegate_info['balance'],
		"manager": conf['pkh'],
		"address": conf['pkh'],
		"alias": conf['name'],
		"percentage": (int (10000. * 100. * float (delegate_info['balance']) / float (delegate_info['staking_balance']))) / 10000.
	})


	return {
		"cycle": cycle,
		"staking_balance": delegate_info['staking_balance'],
		"delegated": delegated
	}



def getBakingAndEndorsmentRights (cycle):
	bak = requests.get (conf['host'] + "/chains/main/blocks/head/helpers/baking_rights?delegate=" + conf['pkh'] + '&cycle=' + str(cycle)).json()
	endors = requests.get (conf['host'] + "/chains/main/blocks/head/helpers/endorsing_rights?delegate=" + conf['pkh'] + '&cycle=' + str(cycle)).json()

	b = list(filter(lambda x: x['priority'] == 0, bak))
	e = endors
	
	return {
		'blocks': b,
		'endorsment': e,
		'estimated_reward': len(b) * BLOCK_REWARD + len(e) * ENDORSMENT_REWARD
	}

def getRewardForPastCycle (cycle):
	return getFrozenBalance (cycle)



if args.action == 'updatedocs':
	curcycle = getCurrentCycle()

	# Load the old docs if any
	try:
		f = open ('docs/data.json', 'r')
		data = json.loads (f.read())
		f.close ()

		lastcycle = max(list(map(lambda y: y['cycle'], data['cycles']))) + 1
		data['cycles'] = list (filter (lambda y: y['cycle'] <= lastcycle, data['cycles']))
	except:
		data = {
			"cycles": []
		}
		lastcycle = int (conf['startcycle'])

	print ('Starting from cycle', lastcycle)

	for cycle in range (lastcycle, getCurrentCycle() + PRESERVED_CYCLES + 1):	
		print ('Updating docs data for cycle', cycle)
		snap = getCycleSnapshot(cycle)
		brights = getBakingAndEndorsmentRights(cycle)

		data['cycles'].append ({
			"cycle": cycle,
			"snapshot": snap,
			"rights": brights
		})

	data['pkh'] = conf['pkh']
	data['name'] = conf['name']
	data['deleguees'] = conf['deleguees']
	data['percentage'] = conf['percentage']
	data['currentcycle'] = curcycle

	f = open ('docs/data.json', 'w')
	f.write (json.dumps(data, separators=(',',':'), indent=4))
	f.close ()

	print ('Up to date')


elif args.action == 'updatependings':
	try:
		f = open ('paylog.json', 'r')
		data = json.loads (f.read())
		f.close ()
	except:
		data = { 'cycle': int (conf['startcycle']) - 1, 'frozen': 0, 'frozenminusfee': 0, 'pendingminusfee': 0, 'pending': 0, 'paid': 0, 'deleguees': {}, 'cycles': {} }

	curcycle = getCurrentCycle()
	data['frozen'] = 0
	data['frozenminusfee'] = 0

	for x in data['deleguees']:
		data['deleguees'][x]['frozen'] = 0

	for cycle in range (data['cycle'] + 1, curcycle):
		print ('Updating for cycle', cycle)
		frozen = (curcycle - cycle - 1) < PRESERVED_CYCLES
		rew = getRewardForPastCycle (cycle)
		
		rewsubfee = int (int (rew['rewards']) - int (rew['rewards']) * (100 - conf['percentage']) / 100.)

		if not frozen:
			data['cycle'] = cycle
			data['pending'] += int (rew['rewards'])
			data['pendingminusfee'] += int (rewsubfee)
		else:
			data['frozen'] += int (rew['rewards'])
			data['frozenminusfee'] += int (rewsubfee)


		data['cycles'][str(cycle)] = {
			'frozenminusfee': rewsubfee if frozen else 0,
			'frozen': int (rew['rewards']) if frozen else 0,
			'rewardminusfee': rewsubfee if not frozen else 0,
			'reward': int (rew['rewards']) if not frozen else 0,
		}

		snap = getCycleSnapshot (cycle)
		for d in snap['delegated']:
			drew = int (rewsubfee * d['percentage'] / 100.)
			if not (d['address'] in data['deleguees']) and ((conf['private'] and d['alias'] != None) or (not conf['private'])):
				data['deleguees'][d['address']] = {
					'address': d['address'],
					'frozen': drew if frozen else 0,
					'pending': drew if not frozen else 0,
					'paid': 0,
					'alias': d['alias'],
					'cycles': { }
				}
				data['deleguees'][d['address']]['cycles'][str(cycle)] = { 'cycle': cycle, 'percentage': d['percentage'], 'balance': d['balance'], 'frozen': drew if frozen else 0, 'reward': drew if not frozen else 0 }
			elif (d['address'] in data['deleguees']) and ((conf['private'] and d['alias'] != None) or (not conf['private'])):
				data['deleguees'][d['address']]['frozen'] += drew if frozen else 0
				data['deleguees'][d['address']]['pending'] += drew if not frozen else 0
				data['deleguees'][d['address']]['cycles'][str(cycle)] = { 'cycle': cycle, 'percentage': d['percentage'], 'balance': d['balance'], 'frozen': drew if frozen else 0, 'reward': drew if not frozen else 0 }


	# Save the paylog
	f = open ('paylog.json', 'w')
	f.write (json.dumps (data, separators=(',',':'), indent=4))
	f.close ()
	f = open ('docs/paylog.json', 'w')
	f.write (json.dumps (data, separators=(',',':'), indent=4))
	f.close ()
	

elif args.action == 'paypendings':
	f = open ('paylog.json', 'r')
	data = json.loads (f.read())
	f.close ()
	
	if data['pendingminusfee'] == 0:
		print ('No pending payments available')
		sys.exit(0)

	print ('There are', formatBalance(data['pendingminusfee']), 'XTZ pending in the pool')
	paydata = ""
	paiddeleguees = 0
	
	for x in data['deleguees']:
		v = data['deleguees'][x]

		if float (formatBalance(v['pending'])) < float(conf['payout']['minpayout']):
			continue

		if conf['payout']['method'] == 'tezos-client':
			if x != conf['pkh']:
				print ('Sending', formatBalance(v['pending']), 'XTZ to', x)
				paydata += 'echo Sending ' + str (formatBalance(v['pending'])) + ' XTZ to ' + x + '\n'
				paydata += './tezos-client transfer ' + str (formatBalance(v['pending'])) + ' from "my_account" to "' + x + '"\n'
				paydata += 'sleep 1\n\n'
			else:
				print ('Not sending', formatBalance(v['pending']), 'XTZ to', x, 'because it\' the pool address')


			data['deleguees'][x]['paid'] += data['deleguees'][x]['pending']
			data['paid'] += data['deleguees'][x]['pending']
			data['pendingminusfee'] -= data['deleguees'][x]['pending']
			data['pending'] -= data['deleguees'][x]['pending']
			data['deleguees'][x]['pending'] = 0 

			paiddeleguees += 1
		else:
			print('Payout method', conf['payout']['method'], 'is not available')
			sys.exit (0)

		

	if paiddeleguees == 0:
		print ('No payments to do, exiting')
		sys.exit (0)

	if conf['payout']['method'] == 'tezos-client':
		f = open ('payouts.sh', 'w')
		f.write (paydata)
		f.close ()
		print ('payouts.sh written; exec the bash command inside to send the transactions.')


	f = open ('paylog.json', 'w')
	f.write (json.dumps (data, separators=(',',':'), indent=4))
	f.close ()
	f = open ('docs/paylog.json', 'w')
	f.write (json.dumps (data, separators=(',',':'), indent=4))
	f.close ()
	print ('paylog.json updated')