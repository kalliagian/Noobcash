import requests
import json
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import node
import sys


HOST_IP = '192.168.0.2'


app = Flask(__name__)

port = int(sys.argv[1])
nodes = int(sys.argv[2])
bootstrap = sys.argv[3]
if bootstrap == 'True':
	b = True
elif bootstrap == 'False':
	b = False
mynode = node.node(port, HOST_IP, nodes, b)



#.......................................................................................


@app.route('/bootstrap/register', methods = ['POST'])
def register():
	params = json.loads(request.data)
	
	address = params['address']
	if address is None:
		return 'Error: Invalid Address', 400
	public_key = params['public_key']
	if public_key is None:
		return 'Error: Invalid Public Key', 400
	try:
		mynode.register_node_to_ring(address, public_key)
		return 'Success', 200
	except:
		return 'Error: Broadcast failed', 400

@app.route('/node/initialization', methods = ['POST'])
def initialization():
	params = json.loads(request.data)
	myid = params['id']
	if  myid is None:
		return 'Error: Invalid ID', 400
	ring = params['ring']
	if ring is None:
		return 'Error: Invalid ring', 400
	public_keys_list = params['public_keys_list']
	if public_keys_list is None:
		return 'Error: Invalid public keys list', 400
	utxos = params['utxos']
	mynode.initialize_net(myid, ring, public_keys_list, utxos)
	return	'Success', 200


@app.route('/node/broadcast/genesis_block', methods = ['POST'])
def broadcast_genesis_block():
	params = json.loads(request.data)
	block = params['block']
	if block is None:
		return 'Error: Invalid genesis block', 400
	current_hash = params['current_hash']
	if current_hash is None:
		return 'Error: Invalid current hash', 400
	mynode.add_genesis_block(block, current_hash)
	return 'Success', 200

@app.route('/node/broadcast/block', methods = ['POST'])
def broadcast_block():
	params = json.loads(request.data)
	block = params['block']
	sender_id = params['id']
	if block is None:
		return 'Error: Invalid block', 400
	block_temp = json.loads(block)
	block = block_temp['block']
	current_hash = block_temp['current_hash']
	if current_hash is None:
		return 'Error: Invalid current hash', 400
	mynode.receive_block(block, current_hash, sender_id)
	return 'Success', 200


@app.route('/node/broadcast_transaction', methods = ['POST'])
def broadcast_transaction():
	params = json.loads(request.data)
	signature = params['signature']
	message = params['message']
	if signature is None:
		return 'Error: Invalid signature', 400
	if message is None:
		return 'Error: Invalid transaction', 400
	mynode.receive_transaction(message, signature)
	return 'Success', 200

@app.route('/node/receive_blockchain', methods = ['POST'])
def receive_blockchain():
	params = json.loads(request.data)
	capacity = params['capacity']
	list_of_blocks = params['list_of_blocks']
	if capacity is None:
		return 'Error: Invalid capacity', 400
	if list_of_blocks is None:
		return 'Error: Invalid list_of_blocks', 400
	mynode.receive_blockchain(capacity, list_of_blocks)
	return 'Success', 200

@app.route('/node/chain_length', methods = ['POST'])
def chain_length():
	params = json.loads(request.data) 
	sender_id = params['id'] 
	if sender_id is None:
		return 'Error: Invalid sender_id', 400
	mynode.receive_chain_length_request(sender_id)	
	return 'Success', 200

@app.route('/node/return_chain_length', methods = ['POST'])
def return_chain_length():
	params = json.loads(request.data)
	chain_length = params['chain_length']
	sender_id = params['id']
	if chain_length is None:
		return 'Error: Invalid chain_length', 400
	if sender_id is None:
		return 'Error: Invalid sender_id', 400
	mynode.lengths.append((chain_length, mynode.ring[sender_id]))
	mynode.responses += 1
	return 'Success', 200
	

@app.route('/node/consensus', methods = ['GET'])
def consensus():
	data = mynode.consensus_data()
	return data


@app.route('/cli/create_transaction', methods = ['POST'])
def create_transaction():
	params = json.loads(request.data)
	receiver = params['receiver']
	if receiver is None:
		return 'Error: Invalid receiver', 400
	amount = params['amount']
	if amount is None:
		return 'Error: Invalid amount', 400
	response = mynode.create_transaction(int(receiver), int(amount))
	if int(receiver) >  mynode.total_nodes or int(receiver) < 0:
		return 'Invalid receiver', 404
	if response == False:
		return 'Not enough money', 400
	else:
		return 'Success', 200

@app.route('/cli/view', methods = ['GET'])
def view():
        data = mynode.view_transactions()
        return data, 200

@app.route('/cli/balance', methods = ['GET'])
def balance():
        data = {
                'amount' : mynode.wallet_balance(mynode.wallet[0])
        }
        data = json.dumps(data)
        return data, 200


@app.route('/cli/get_id', methods = ['GET'])
def get_id():
        data = {
                'id' : mynode.id
        }
        data = json.dumps(data)
        return data, 200


#for frontend

@app.route('/', methods=['GET'])
def home():
    bal = mynode.wallet_balance(mynode.wallet[0])

    data = {
        'ADDRESS': 'http://' + str(mynode.ip) +':' + str(mynode.port) ,
        'NO_OF_NODES':  len(set(mynode.ring)),
        'ID': mynode.id,
        'SENDER': mynode.wallet[0],
        'OTHERSK': mynode.public_keys_list,
        'bal': bal,

    }
    return render_template('index.html', data=data)

@app.route('/transaction', methods=['GET'])
def transa():
    bal = mynode.wallet_balance(mynode.wallet[0])

    data = {
        'ADDRESS': 'http://' + str(mynode.ip) +':' + str(mynode.port) ,
        'NO_OF_NODES':  len(set(mynode.ring)),
        'ID': mynode.id,
        'SENDER': mynode.wallet[0],
        'OTHERSK': mynode.public_keys_list,
        'bal': bal,

    }
    return render_template('transaction.html', data=data)

@app.route('/view', methods=['GET'])
def vie():
    trns = json.loads(mynode.view_transactions())
    trns_li = trns['listOfTransactions']
    bal = mynode.wallet_balance(mynode.wallet[0])

    data = {
        'ADDRESS': 'http://' + str(mynode.ip) +':' + str(mynode.port) ,
        'NO_OF_NODES':  len(set(mynode.ring)),
        'ID': mynode.id,
        'SENDER': mynode.wallet[0],
        'OTHERSK': mynode.public_keys_list,
        'bal': bal,
		'tr_list' : trns_li,
    }
    return render_template('view.html', data=data)

@app.route('/balance', methods=['GET'])
def bala():
    bal = mynode.wallet_balance(mynode.wallet[0])

    data = {
        'ADDRESS': 'http://' + str(mynode.ip) +':' + str(mynode.port) ,
        'NO_OF_NODES':  len(set(mynode.ring)),
        'ID': mynode.id,
        'SENDER': mynode.wallet[0],
        'OTHERSK': mynode.public_keys_list,
        'bal': bal,

    }
    return render_template('balance.html', data=data)


@app.route('/create_transaction_site', methods=['POST'])
def site_transaction():
    print('MEOW')
    params = json.loads(request.data)
    receiver = params['receiver']
    amount = params['nbc']

    if not amount.isnumeric():
        return jsonify('Error: Invalid amount of money'), 400

    else:
        transa = {'receiver': receiver, 'amount': int(amount)}
        print(transa)
        transa = json.dumps(transa)
        print(transa)
        response = mynode.create_transaction(int(receiver), int(amount))

    return jsonify('OKEIII'), 200


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
