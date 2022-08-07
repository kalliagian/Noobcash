from Crypto.PublicKey import RSA
import hashlib
import sys
import json
import requests
import threading
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from base64 import b64encode
import transaction
import blockchain
import block
import time
'''
import block
import wallet
'''

BOOTSTRAP_IP = 'http://192.168.0.2:'
BOOTSTRAP_PORT = '5000' 

class node:
	def __init__(self, port, ip, total_nodes=4, bootstrap=False):
		self.chain = blockchain.Blockchain()
		self.total_nodes = total_nodes
		print('Initializing Noobcash net...')
		self.ip = ip
		self.port = port
		self.wallet = self.create_wallet()
		self.public_keys_list = []
		self.ring = [BOOTSTRAP_IP + BOOTSTRAP_PORT] 
		self.utxos = dict()
		self.temp_last_block = []	
		self.temp_queue = []
		self.chain_length_requests_queue = []
		self.responses = 0
		self.utxos[self.wallet[0]] = []
		self.event_my_mine = threading.Event()
		self.event_receive_mine = threading.Event()	
		self.mine_thread = threading.Thread(target = self.mine_my_block) 
		self.event_mining_take_place = threading.Event()

		if bootstrap:
			self.id = 0
			self.seen = 0
			self.public_keys_list = [self.wallet[0]]
			self.utxos = {key : [] for key in self.public_keys_list}
			self.genesis_block = self.create_genesis_block()
			self.chain.add_block(self.genesis_block)
			self.last_block = self.create_new_block()
			genesis_utxo = {
				'id' : self.genesis_block.listOfTransactions[0].transaction_id,
				'amount' : self.genesis_block.listOfTransactions[0].amount
			}
			self.utxos[self.wallet[0]].append(genesis_utxo)
			self.event = threading.Event()
			thread = threading.Thread(target = self.start_broadcast)
			thread.start()

		else:
			self.register()


	def register(self):
		data = {
			'address': "http://" + self.ip + ":" + str(self.port),
			'public_key': self.wallet[0]
		}
		data = json.dumps(data)
		print('Registering...')
		return requests.post(self.ring[0] + "/bootstrap/register", data = data)
			

	@staticmethod
	def create_wallet():
		key = RSA.generate(2048)
		private_key = key.exportKey('PEM').decode()
		public_key = key.publickey().exportKey('PEM').decode()
		return public_key, private_key


	def register_node_to_ring(self, address, public_key):
		print('Register a new node')
		self.ring.append(address)
		self.public_keys_list.append(public_key)
		self.seen += 1
		self.utxos[public_key] = []
		self.create_transaction(self.seen, 100, True)
		if self.seen == self.total_nodes:
			self.event.set()
		return

	def broadcast_blockchain(self):
		data = self.chain.forSend()
		for ip in self.ring[1:]:
			response = requests.post(ip + '/node/receive_blockchain', data = data)
		return


	def start_broadcast(self):
		self.event.wait()
		time.sleep(1)
		self.broadcast()
		self.broadcast_blockchain()
		print('Initialized net')
		return


	def broadcast(self):
				
		for cnt, ip in enumerate(self.ring[1:]):
			utxos_for_send = dict()
			for utxo in self.utxos:
				utxos_for_send[utxo] = [{'id' : x['id'].hexdigest(), 'amount' : x['amount']} for x in self.utxos[utxo]]
			data = {
				'id' : cnt + 1,
				'ring' : self.ring,
				'public_keys_list' : self.public_keys_list,
				'utxos' : utxos_for_send
			}
			data = json.dumps(data)
			response = requests.post(ip + '/node/initialization', data = data)
		return


	def initialize_net(self, myid, ring, public_keys_list, utxos):
		self.id = myid
		self.ring = ring
		self.public_keys_list = public_keys_list
		self.utxos = utxos 
		return

	def create_genesis_block(self):
		nbcs = 100 * (self.total_nodes + 1)
		genesis_transaction = transaction.Transaction('0', self.wallet[0],value = nbcs, genesis = True)
		genesis_block = block.Block(index = 0, nonce = 0, previousHash = 1, capacity = 1, genesis = True)
		genesis_block.add_transaction(genesis_transaction)
		return genesis_block
	
	def add_genesis_block(self, blk, current_hash):
		blk_obj = block.to_object(blk, current_hash = current_hash, genesis = True)
		self.chain.add_block(blk_obj)
		self.utxos[self.public_keys_list[0]].append({'id' : blk_obj.listOfTransactions[0].transaction_id, 'amount' : blk_obj.listOfTransactions[0].amount})
		self.last_block = self.create_new_block()
		return

	def receive_blockchain(self, capacity, list_of_blocks):
		chain =	blockchain.to_object(capacity, list_of_blocks)
		self.chain = blockchain.Blockchain(capacity=capacity, list_of_blocks=[])
		self.chain.add_block(chain.list_of_blocks[0])
		self.last_block = chain.list_of_blocks[0]
		if not self.validate_chain(chain):
			return
		self.last_block = self.create_new_block()
		print('Initialized net')
		return
		
	def validate_chain(self, chain):
		for blk in chain.list_of_blocks[1:]:
			if not self.validate_block(blk, blk.hash, self.id):
				return False
			self.chain.add_block(blk)
		return True				

	def create_transaction(self, receiver, amount, first_trans = False):
		receiver_key = self.public_keys_list[receiver]
		idx = -1
		t_sum = 0
		inputs = []
		for i, trans in enumerate(self.utxos[self.wallet[0]]):
			t_sum += trans['amount']
			inputs.append(trans['id'])
			if t_sum >= amount:
				rest = t_sum - amount
				idx = i
				break
		if t_sum < amount:
			return False
		outputs = [{'address' : receiver_key, 'amount' : amount}, {'address' : self.wallet[0], 'amount' : rest}]
		trans = transaction.Transaction(self.wallet[0], receiver_key, self.wallet[1], amount, inputs, outputs)
		d = {'id' : trans.transaction_id, 'amount' : rest}
		if idx + 1 == len(self.utxos[self.wallet[0]]):
			self.utxos[self.wallet[0]] = [d]
		else:
			self.utxos[self.wallet[0]] = [d] + self.utxos[self.wallet[0]][idx + 1:]
		self.utxos[receiver_key].append({'id' : trans.transaction_id, 'amount' : amount})
		self.add_transaction_to_block(trans)
		if not first_trans:
			self.transaction_for_broadcast = trans
			broadcast_transaction_thread = threading.Thread(target = self.broadcast_transaction_thread_func)
			broadcast_transaction_thread.start()
		self.check_full_block(first_trans)
		return trans

	def broadcast_transaction_thread_func(self):
		self.broadcast_transaction(self.transaction_for_broadcast)
		return

	def broadcast_transaction(self, trans):
		data = trans.forSend()
		data = json.dumps(data)
		url = '/node/broadcast_transaction'
		for ip in self.ring:
			if ip != "http://" + self.ip + ":" + str(self.port):
				response = requests.post(ip + url, data = data)
		return response

	def receive_chain_length_request(self, sender_id) : 
		if self.event_mining_take_place.isSet():
			self.chain_length_requests_queue.append(sender_id)
			return
		requests.post(self.ring[sender_id] + '/node/return_chain_length', data = json.dumps({'chain_length' : len(self.chain.list_of_blocks), 'id' : self.id}))
		return

	def receive_transaction(self, message, signature):
		sender_address = message['sender_address']
		if self.event_mining_take_place.isSet():
			self.temp_queue.append([message, signature])
			return
		if not self.validate_transaction(sender_address, message, signature):
			return	
		signature = transaction.preproccess_receiver_signature(signature)
		trans = transaction.to_object(message, signature)
		self.add_transaction_to_block(trans)
		self.check_full_block()
		return

	def verify_signature(self, sender, message, signature):
		signature = transaction.preproccess_receiver_signature(signature)
		message = SHA.new(transaction.preproccess_trans_format_dict_for_hashing(message))
		key = RSA.importKey(sender)
		return PKCS1_v1_5.new(key).verify(message, signature)
	
	def validate_transaction(self, sender_address, message, signature):
		verified = self.verify_signature(sender_address, message, signature)
		if not verified:
			return False
		trans_inputs = message['transaction_inputs']
		ids_list = []
		for x in self.utxos[sender_address]:
			if type(x['id']) != str and type(x['id']) != int:
				ids_list.append(x['id'].hexdigest()) 
			else:
				ids_list.append(x['id'])
		trans_amount = message['amount']
		t_sum = 0
		idxs_deleted = []
		for input_id in trans_inputs:
			if not (input_id in ids_list):
				return False
			idx = ids_list.index(input_id)
			t_sum += self.utxos[sender_address][idx]['amount']
			idxs_deleted.append(idx)

		if t_sum < trans_amount:
			return False

		for idx in idxs_deleted:
			del self.utxos[sender_address][idx]

		trans_id = SHA.new(transaction.preproccess_trans_format_dict_for_hashing(message))
		trans_outputs = message['transaction_outputs']
		for output in trans_outputs:
			address = output['address']
			amount = output['amount']
			self.utxos[address].append({'id' : trans_id, 'amount' : amount})
		return True


	def add_transaction_to_block(self, trans):
		self.last_block.add_transaction(trans)
		return

		
	def check_full_block(self, first_trans = False):
		if not self.last_block.full:
			return False
		self.event_my_mine.clear()
		self.event_receive_mine.clear()
		mine_thread = threading.Thread(target = self.mine_my_block)
		self.prevHash_mining_block = self.last_block.previousHash.hexdigest() if type(self.last_block.previousHash) != str and type(self.last_block.previousHash) != int else self.last_block.previousHash
		self.event_mining_take_place.set()
		mine_thread.start()
		self.control_mine(first_trans)
		return True


	def control_mine(self, first_trans = False):
		while(True):
			if self.event_my_mine.isSet():
				break
		self.event_mining_take_place.clear()
		if self.event_receive_mine.isSet():
			self.last_block = self.create_new_block()
			self.event_receive_mine.clear()
			self.event_my_mine.clear()	
			self.event_mining_take_place.clear()
			return	

		self.event_mining_take_place.clear()
		send_chain_length_queue_thread = threading.Thread(target = self.send_chain_length_queue) 
		send_queue_transactions_thread = threading.Thread(target = self.send_queue_transactions)
		send_queue_transactions_thread.start()
		send_chain_length_queue_thread.start() 
		if not self.validate_block(self.last_block, self.last_block.hash, self.id):
			if len(self.last_block.listOfTransactions) == self.chain.capacity:
				self.last_block = self.create_new_block()
			self.event_my_mine.clear()
			self.event_receive_mine.clear()
			return
		self.chain.add_block(self.last_block)
		if not first_trans:
			self.broadcast_block(self.last_block)
		self.last_block = self.create_new_block()
		self.event_my_mine.clear()
		self.event_receive_mine.clear()
		return

	def send_chain_length_queue(self): 
		while len(self.chain_length_requests_queue) != 0:
			data = {
				'chain_length' : len(self.chain.list_of_blocks),
				'id' : self.id
			}
			index = self.chain_length_requests_queue.pop()
			requests.post(self.ring[index] + '/node/return_chain_length', data=json.dumps(data))
		return


	def send_queue_transactions(self):
		while len(self.temp_queue) != 0:
			trans = self.temp_queue.pop()
			self.receive_transaction(trans[0], trans[1])
		return
		


	def mine_my_block(self):
		self.mine_block(self.event_my_mine, self.event_receive_mine)
		return


	def create_new_block(self):
		prevHash = self.chain.get_hash_of_last_block()
		lastIndex = self.chain.get_last_index()
		blk  = block.Block(index = lastIndex + 1, nonce = -1, previousHash = prevHash, capacity = self.chain.capacity, listOfTransactions = [])
		return blk


	def receive_block(self, blk, current_hash, sender_id):
		blk_obj = block.to_object(blk, current_hash)
		if not self.validate_block(blk_obj, current_hash, sender_id):
			return 
		self.chain.add_block(blk_obj)	
		self.event_receive_mine.set()
		return

	
	def broadcast_block(self, blk, genesis = False):
		if genesis:
			url = '/node/broadcast/genesis_block'
		else:
			url = '/node/broadcast/block'

		data = {
			'block' : blk.forSend(), 
			'id' : self.id
		}
		data = json.dumps(data)
		for ip in self.ring:
			if ip != "http://" + self.ip + ":" + str(self.port):
				response = requests.post(ip + url, data = data)
		return response

	def mine_block(self, event_my_mine, event_receive_mine):
		if self.last_block.mine_block(event_receive_mine):
			event_my_mine.set()
			#f = open("block_times.txt", "a")
			#f.write(str(time.time()) + '\n')
			return True
		else:
			if self.event_receive_mine.isSet():	
				#f = open("block_times.txt", "a")
				#f.write(str(time.time()) + '\n')
				event_my_mine.set()
				return False
		return False

	def validate_block(self, blk, current_hash, sender_id):
		hash_id = SHA.new(blk.to_dict().encode())
		if type(current_hash) != str and type(current_hash) != int:
			current_hash = current_hash.hexdigest()
		if hash_id.hexdigest() != current_hash:
			return False
		prevHash = self.chain.get_hash_of_last_block()
		#prev_prevHash = self.chain.list_of_blocks[-1].previousHash
		if type(prevHash) != str and type(prevHash) != int:
			prevHash = prevHash.hexdigest()
		#if type(prev_prevHash) != str and type(prev_prevHash) != int:
		#	prev_prevHash = prev_prevHash.hexdigest()
		if type(blk.previousHash) != str and type(blk.previousHash) != int:
			blk_previousHash = blk.previousHash.hexdigest()
		else:
			blk_previousHash = blk.previousHash
		if blk_previousHash != prevHash:
			self.resolve_conflict()
			return False
		return True

	def resolve_conflict(self):
		max_length = -1 
		max_ip = '' 
		self.responses = 0 
		self.lengths = [] 
		for ip in self.ring:
			if ip != "http://" + self.ip + ":" + str(self.port):
				requests.post(ip + '/node/chain_length', data=json.dumps({'id' : self.id})) 

		while(True):
			if(self.responses >= self.total_nodes):
				break
		for (length, ip) in self.lengths:
			if length > max_length:
				max_length = length
				max_ip = ip
			elif length == max_length:
				l = [3, 1, 4, 2, 5]
				if l[int(max_ip.split(':')[1][-1]) - 1] > l[int(ip.split(':')[1][-1]) - 1]:
					max_length = length
					max_ip = ip

		response = requests.get(max_ip + '/node/consensus')
		text = json.loads(response.text)
		chain = json.loads(text['chain'])
		last_block = json.loads(text['last_block'])
		blk = last_block['block']
		current_hash = last_block['current_hash']
		self.utxos = text['utxos']
		capacity = chain['capacity']
		list_of_blocks = chain['list_of_blocks']
		self.chain = blockchain.to_object(capacity, list_of_blocks)
		
		self.last_block = block.to_object(blk, current_hash=current_hash)
		return

	def consensus_data(self):
		utxos_for_send = dict()
		for utxo in self.utxos:
			utxos_for_send[utxo] = [{'id' : x['id'].hexdigest() if type(x['id']) != str and type(x['id']) != int else x['id'], 'amount' : x['amount']} for x in self.utxos[utxo]]
		data = {
			'utxos' : utxos_for_send,
			'last_block' : self.last_block.forSend(),
			'chain' : self.chain.forSend()
		}
		return json.dumps(data)
			

	def view_transactions(self):
		list_trans = []
		for cnt, trans in enumerate(self.chain.list_of_blocks[-1].listOfTransactions):
			message = trans.forSend()
			hash_id = SHA.new(transaction.preproccess_trans_format_dict_for_hashing(message['message']))
			t = {'content' : message['message'], 'hash_id' : hash_id.hexdigest()}
			list_trans.append(t)
		data = {'listOfTransactions' : list_trans}
		return json.dumps(data)




	def wallet_balance(self, public_key):
		t_sum = 0
		for utxo in self.utxos[public_key]:
			t_sum += utxo['amount']
		return t_sum

