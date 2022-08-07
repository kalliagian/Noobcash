from collections import OrderedDict

import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request, render_template
import json
import hashlib


def preproccess_trans_for_hashing(msg):
	msg['transaction_inputs'] = [x.hexdigest() if type(x) != str else x  for x in msg['transaction_inputs']]
	return json.dumps(msg).encode()

def preproccess_trans_format_dict_for_hashing(msg):
	return json.dumps(msg).encode()

def preproccess_sender_signature(signature):
	if type(signature) != str and type(signature) != int:
		return signature.decode('latin-1')
	return signature

def preproccess_receiver_signature(signature):
	return signature.encode('latin-1') 

def to_object(dictionary, signature = -1,genesis = False):
	sender_address  = dictionary['sender_address']
	receiver_address = dictionary['receiver_address']
	amount = dictionary['amount']
	transaction_inputs = dictionary['transaction_inputs']
	transaction_outputs = dictionary['transaction_outputs']
	return Transaction(sender_address = sender_address, receiver_address = receiver_address, value = amount, transaction_inputs = transaction_inputs, transaction_outputs = transaction_outputs, signature = signature, genesis = genesis)



class Transaction:
	
	def __init__(self, sender_address, receiver_address, sender_private_key = -1, value = -1, transaction_inputs = [], transaction_outputs = [], signature = -1, genesis = False):
		self.genesis = genesis
		self.sender_address = sender_address
		self.receiver_address = receiver_address
		self.sender_private_key = sender_private_key
		self.amount = value
		self.transaction_inputs = transaction_inputs
		self.transaction_outputs = transaction_outputs
		self.transaction_id = -1
		self.hash_transaction() 
		self.signature = signature
		if (not self.genesis) and self.signature == -1 and sender_private_key != -1:
			self.sign_transaction()


	def to_dict(self):
		data = {
			'sender_address' :  self.sender_address,
			'receiver_address' : self.receiver_address,
			'amount' : self.amount,
			'transaction_inputs' : self.transaction_inputs,
			'transaction_outputs' : self.transaction_outputs
		}
		return data
	
	def to_dict_for_hash_block(self):
		data = {
			'sender_address' : self.sender_address,
			'receiver_address' : self.receiver_address,
			'amount' : self.amount,
			'transaction_inputs' : [x.hexdigest() if type(x) != str and type(x) != int else x for x in self.transaction_inputs],
			'transaction_outputs' : self.transaction_outputs
		}
		return data
	
	def to_json(self):
		return json.dumps(self.to_dict())

	def forSend(self):
		d = self.to_dict()
		d['transaction_inputs'] = [x.hexdigest() if type(x) != str and type(x) != int else x for x in d['transaction_inputs']]
		data = {
			'signature' : preproccess_sender_signature(self.signature), 
			'message' : d
		}
		return data


	def hash_transaction(self):
		obj = preproccess_trans_for_hashing(self.to_dict()) 
		self.transaction_id = SHA.new(obj)
		return self


	def sign_transaction(self):
		key = RSA.importKey(self.sender_private_key)
		self.signature = PKCS1_v1_5.new(key).sign(self.transaction_id)
		return self

	def verify_transaction(self, public_key):
		key = RSA.importKey(public_key)
		return PKCS1_v1_5.new(key).verify(self.transaction_id, self.signature)


