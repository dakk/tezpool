# TezPool
TezPool is an opensource redistribution software for tezos baking pools.


## Configuration
The software is configured by modifying the config.json file.

- host: the host of your node; if you run the pool in the same server of the node, leave "http://127.0.0.1:8732"
- pkh: publickeyhash of the delegate
- name: name of your pool (debug only)
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

Estimate the reward for cycle 8:

```bash
python3 tezpool.py --cycle 8 estimate
```

Get the splitting percentages for cycle 8:

```bash
python3 tezpool.py --cycle 8 percentage
```


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

