#!/usr/bin/python3

# http://doc.tzalpha.net/api/rpc_proposal.html?highlight=june
# http://doc.tzalpha.net/api/rpc.html#usage

import json
import time
import argparse
import sys
import requests

# Constants
DEBUG = False
PRESERVED_CYCLES = 5
BLOCK_REWARD = 16 * 1000000.
ENDORSMENT_REWARD = 2 * 1000000.
BLOCKS_PER_CYCLE = 4096

# Income/Rewards Breakdown
idx_income_expected_income = 19
idx_income_total_income = 21
idx_income_total_bonds = 22

idx_income_baking_income = 23
idx_income_endorsing_income = 24
idx_income_double_baking_income = 25
idx_income_double_endorsing_income = 26
idx_income_seed_income = 27
idx_income_fees_income = 28
idx_income_missed_baking_income = 29
idx_income_missed_endorsing_income = 30
idx_income_stolen_baking_income = 31

idx_income_total_lost = 32
idx_income_lost_accusation_fees = 33
idx_income_lost_accusation_rewards = 34
idx_income_lost_accusation_deposits = 35
idx_income_lost_revelation_fees = 36
idx_income_lost_revelation_rewards = 37

# Cycle Snapshot
idx_balance = 0
idx_baker_delegated = 1
idx_delegator_address = 2

# Current balances
idx_cb_delegator_id = 0
idx_cb_current_balance = 1
idx_cb_delegator_address = 2

# Rights
idx_r_type = 1
idx_r_priority = 4

# Flow
idx_f_category = 9
idx_f_amount_in = 11
# idx_f_amount_out = 12
# idx_f_frozen = 19

TZSTAT_API = 'http://api.tzstats.com'
TZSTAT_EP = {
	'rights': '{}/tables/rights?address={}&cycle={}&limit=1000',
	'rewards': '{}/tables/income?address={}&cycle={}',
	'delegates': '{}/tables/snapshot?cycle={}&is_selected=1&baker={}&columns=balance,delegated,address&limit=50000',
	'bbalance': '{}/tables/account?delegate={}&columns=row_id,spendable_balance,address',
	'cbalance': '{}/tables/account?address={}&columns=row_id,spendable_balance,address',
	'flow': '{}/tables/flow?address={}&cycle={}&limit=1000'
}

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

def try_get(uri, try_n=5):
	if 'http' not in uri:
		uri = conf['host'] + uri

	if DEBUG:
		print ('=> try_get:', uri)

	try:
		return requests.get (uri).json()
	except:
		if try_n > 0:
			if DEBUG:
				print ('Get failed, retrying %d' % try_n)
			return try_get(uri, try_n - 1)
		else:
			raise Exception('Reached max retries for get request: ' + uri)


def formatBalance (bal):
	return str (int (bal) / 1000000)


def getCurrentCycle ():
	return try_get ('/chains/main/blocks/head/helpers/current_level')['cycle']


def getFrozenBalance(cycle):
	flow = try_get(TZSTAT_EP['flow'].format(TZSTAT_API, conf['pkh'], cycle))
	# print (flow)
	flow = list(filter(lambda x: x[idx_f_category] == 'rewards', flow))
	#  and x[idx_f_frozen] == 1
	fr_amount = 0.0
	for x in flow:
		fr_amount += x[idx_f_amount_in] #- x[idx_f_amount_out]

	fr_amount = fr_amount * 1000000

	print ('Cycle: {}\tReward: {} tz'.format(cycle, formatBalance(fr_amount)))

	return {
		'rewards': fr_amount
	}


def getCycleSnapshot(cycle):
	delegate_info = try_get (TZSTAT_EP['delegates'].format(TZSTAT_API, cycle, conf['pkh']))
	delegated = []
	staking_balance = 0

	for x in delegate_info:
		staking_balance += float(x[idx_balance])
	staking_balance = int(staking_balance * 1000000.)

	print ('Staking balance for cycle {}: {} tz'.format(cycle, formatBalance(staking_balance)))


	# Get the delegated balance of each contract
	for x in delegate_info:
		addr = x[idx_delegator_address]
		bal = float(x[idx_balance]) * 1000000.

		contract_info2 = {
			"balance": int(bal), #x['balance'],
			# "manager": contract_info['manager'],
			"address": addr,
			"alias": conf['deleguees'][addr] if (addr in conf['deleguees']) else None,
			"percentage": (int (10000. * 100. * bal / float(staking_balance))) / 10000.
		}
		delegated.append(contract_info2)
		print ('Cycle: {}\tAddress: {}\tBalance: {}\tPercentage: {}%'.format(
			cycle, addr, formatBalance(bal), contract_info2['percentage']))


	# Assert the sum of percentage is 100%
	perc = 0.0
	for x in delegated:
		perc += x['percentage']

	if perc < 99.9:
		raise Exception("Percentage is not 100%!")

	return {
		"cycle": cycle,
		"staking_balance": staking_balance,
		"delegated": delegated
	}


def getBakingAndEndorsmentRights (cycle, curcycle):
	rights = try_get (TZSTAT_EP['rights'].format(TZSTAT_API, conf['pkh'], cycle))
	rights = list(filter(lambda x: x[idx_r_type] == 'endorsing' or (x[idx_r_type] == 'baking' and x[idx_r_priority] == 0), rights))

	b = []
	e = []

	for x in rights:
		if x[idx_r_type] == 'baking':
			b.append(x[2])
		elif x[idx_r_type] == 'endorsing':
			e.append(x[2])

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

	for cycle in range (lastcycle, getCurrentCycle() - 1): # + PRESERVED_CYCLES + 1):
		print ('Updating docs data for cycle', cycle)
		snap = getCycleSnapshot(cycle)
		time.sleep(0.5)
		brights = getBakingAndEndorsmentRights(cycle, curcycle)
		time.sleep(0.5)

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
		data = { 
			'cycle': int (conf['startcycle']) - 1,
			'frozen': 0,
			'frozenminusfee': 0,
			'pendingminusfee': 0,
			'pending': 0,
			'paid': 0,
			'deleguees': {},
			'cycles': {}
		}

	curcycle = getCurrentCycle()
	data['frozen'] = 0
	data['frozenminusfee'] = 0

	for x in data['deleguees']:
		data['deleguees'][x]['frozen'] = 0

	for cycle in range (data['cycle'] + 1, curcycle - 1):
		print ('Updating for cycle', cycle)
		frozen = (curcycle - cycle - 1) < PRESERVED_CYCLES
		try:
			rew = getRewardForPastCycle (cycle)
			time.sleep(0.5)
		except:
			print ('Cant get reward for cycle', cycle)
			continue

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
		time.sleep(0.5)
		for d in snap['delegated']:
			drew = int (rewsubfee * d['percentage'] / 100.)
			if not (d['address'] in data['deleguees']) and ((conf['private'] and d['alias'] is not None) or (not conf['private'])):
				data['deleguees'][d['address']] = {
					'address': d['address'],
					'frozen': drew if frozen else 0,
					'pending': drew if not frozen else 0,
					'paid': 0,
					'alias': d['alias'],
					'cycles': { }
				}
				data['deleguees'][d['address']]['cycles'][str(cycle)] = { 'cycle': cycle, 'percentage': d['percentage'], 'balance': d['balance'], 'frozen': drew if frozen else 0, 'reward': drew if not frozen else 0 }
			elif (d['address'] in data['deleguees']) and ((conf['private'] and d['alias'] is not None) or (not conf['private'])):
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
				paydata += conf['payout']['tezos_client'] + ' transfer ' + str (formatBalance(v['pending'])) + ' from "' + conf['payout']['from_account'] + '" to "' + x + '"\n'
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
