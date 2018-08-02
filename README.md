# TezPool
TezPool is an opensource redistribution software for tezos baking pools.


## Configuration
The software is configured by modifying the config.json file.

- host: the host of your node; if you run the pool in the same server of the node, leave "http://127.0.0.1:8732"
- pkh: publickeyhash of the delegate
- name: name of your pool
- percentage: % of tezos to distribute
- payto: could be "contract" if you want to pay rewards to KT addresses, or "manager" if you want to pay reward to tz addresses
- deleguees: a dictionary with "address": "alias"
- private: true if you want to split the reward only between addresses defined in deleguees

## Install

```bash
git clone https://github.com/dakk/tezpool
cd tezpool
apt-get install python3-pip
pip3 install requests
```

## Usage

```bash
usage: tezpool.py [-h] [-c config.json] [-cc cycle] action

Tezos delegate redistribution script

positional arguments:
  action                action to perform (updatedocs, updatependings, paypendings)

optional arguments:
  -h, --help            show this help message and exit
  -c config.json, --config config.json
                        set a config file (default: config.json)
```


Update the docs; this command will update the frontend with future cycles and reward estimation:

```bash
python3 tezpool.py updatedocs
```

Update the frozen / pending reward for deleguees; it will edit/generate a file called paylog.json which
contains pool payment data:

```bash
python3 tezpool.py updatependings
```

Pay pending reward (unfrozen rewards); it will edit paylog.json subtracting pending reward and sending transactions
to delegators (still WIP):

```bash
python3 tezpool.py paypendings
```

For every new cycle you have to run both updatedocs and updatependings, and upload the new frontend data.


## Frontend
The docs/ folder contains a tiny frontend for the pool statistics; you have to run the updatedocs action in order to keep the frontend updated.


## Donate
This software is free and opensource, but donations are always appreciated;
these are my donation addresses:
- Tezos: tz1THsLcunLo8CmDm9f2y1xHuXttXZCpyFnq
- Bitcoin: 13TRVwiqLMveg9aPAmZgcAix5ogKVgpe4T
- Ethereum: 0x18F081247ad32af38404D071eb8c246CC4F33534

## License
Copyright 2018 Davide Gessa

Permission is hereby granted, free of charge, to any person obtaining a 
copy of this software and associated documentation files (the 
"Software"), to deal in the Software without restriction, including 
without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to 
the following conditions:

The above copyright notice and this permission notice shall be included 
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

