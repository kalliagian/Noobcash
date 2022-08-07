import blockchain
import time
import json
from Crypto.Hash import SHA
import transaction

DIFFICULTY = 4
CAPACITY = 10

def to_object(dictionary, current_hash = -1, genesis = False):
	index = dictionary['index']
	timestamp = dictionary['timestamp']
	listOfTrans = [transaction.to_object(x, genesis = genesis) for x in dictionary['listOfTransactions']]
	nonce = dictionary['nonce']
	prevHash = dictionary['previousHash']
	return Block(index = index, nonce = nonce, previousHash = prevHash, capacity = CAPACITY, current_hash = current_hash, timestamp = timestamp, listOfTransactions = listOfTrans, genesis = genesis)



class Block:
	def __init__(self, index, nonce, previousHash, capacity, current_hash = -1, timestamp = time.time(), listOfTransactions = [], genesis = False):
		##set
		self.genesis = genesis
		self.index = index
		self.previousHash = previousHash
		self.timestamp = timestamp
		self.hash = current_hash #initialization
		self.nonce = nonce
		self.capacity = capacity
		self.full = False
		self.listOfTransactions = listOfTransactions
	
	def to_dict(self):
		data = {
			'index' : self.index,
			'timestamp' : self.timestamp,
			'listOfTransactions' : [trans.to_dict_for_hash_block() for trans in self.listOfTransactions],
			'nonce' : self.nonce,
			'previousHash' : self.previousHash if type(self.previousHash) == str or type(self.previousHash) == int else self.previousHash.hexdigest()
		}
		return json.dumps(data)

	def forSend(self):
		data = {
			'current_hash' : self.hash.hexdigest() if type(self.hash) != int and type(self.hash) != str else self.hash,
			'block' : json.loads(self.to_dict())
		}
		return json.dumps(data)


	def myHash(self):
		#calculate self.hash
		obj = self.to_dict()
		self.hash = SHA.new(obj.encode())
		return self		



	def add_transaction(self, transaction):
		#add a transaction to the block
		self.listOfTransactions.append(transaction)
		
		if len(self.listOfTransactions) == self.capacity:
			self.full = True
			if self.genesis:
				self.myHash()
		return self

	def mine_block(self, event_receive_mine):
		self.nonce = 0
		while(True):
			self.myHash()	
			if self.hash.hexdigest()[:DIFFICULTY] == DIFFICULTY * '0':
				self.full = True
				break
			else:
				self.nonce += 1
			if event_receive_mine.isSet():
				return False
		return True



