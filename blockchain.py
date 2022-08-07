from block import Block
from transaction import Transaction
import json, requests, time
import threading
import node
import block

CAPACITY = 10


def to_object(capacity, list_of_blocks):
	my_list = []
	for cnt, blk in enumerate(list_of_blocks):
		blk_dict = json.loads(blk)
		current_hash = blk_dict['current_hash']
		b = blk_dict['block']
		if cnt == 0:
			blk_object = block.to_object(b, current_hash, True)
		else:
			blk_object = block.to_object(b, current_hash, False)
		my_list.append(blk_object)
	chain = Blockchain(capacity, my_list)
	return chain

class Blockchain():
	
	def __init__(self, capacity = CAPACITY, list_of_blocks = []):
		self.list_of_blocks = list_of_blocks
		self.capacity = capacity		
#		self.f = open("block_times.txt", "a")		

	def forSend(self):
		data = {
			'capacity' : self.capacity,
			'list_of_blocks' : [x.forSend() for x in self.list_of_blocks]
		}
		return json.dumps(data)

	def get_hash_of_last_block(self):
		return self.list_of_blocks[-1].hash
	
	def get_last_index(self):
		return self.list_of_blocks[-1].index

	def add_block(self, block):
		#print('BLOCK TO ADD', block.to_dict())
		self.list_of_blocks.append(block)
#		self.f.write(str(time.time()) + '\n')
		for blk in self.list_of_blocks:
			b = blk.listOfTransactions[-1].transaction_id
			if type(b) != str and type(b) != int:
				b = b.hexdigest()
			if type(blk.hash) != str and type(blk.hash) != int:
				a = blk.hash.hexdigest()
				print("BLOCK NONCE--------: ",blk.nonce," CURRENT HASHH:",a)
				print("CURRENT TRANSACTION HASH-------:", b)
				print("AMOUNT OF LAST TRANSACTION-----------:", blk.listOfTransactions[-1].amount)
			else:
				print("BLOCK NONCE--------: ", blk.nonce, "CURRENT HASH:", blk.hash)
				print("CURRENT TRANSACTION HASH---------:", b)
				print("AMOUNT OF LAST TRANSACTION----------:", blk.listOfTransactions[-1].amount)
		return


