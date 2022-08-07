import click
#import paths
#import os.path
#import os
import requests
import validation
import json
#import csv
#import time
import node
import time
import os

HOST_IP = '192.168.0.2'
@click.group()
def cli():

	"""\b
	-------------------------------------------
	Hello we are team 28. Welcome to NOOBCASH CLI!
	-------------------------------------------
	\b
	This is a Command Line tool we developed
	for some basic functions of our system. 
	\b
	For more information about each command
	use the --help option:
	noobcash [COMMAND] --help
	\b
	-------------------------------------------
	TEAM MEMBERS:
	Christodoulea Effrosyni
	Giannakopoulou Kalliopi-Eleftheria
	Kritharoula Anastasia
	-------------------------------------------
	"""

	pass
    

@cli.command(short_help='Create a new node')
@click.option('--port', required=True, help='Enter port', metavar ='[XXXX]')
@click.option('--bootstrap', type=click.Choice(['True', 'False'], case_sensitive=True), required=True, help = 'Enter flag for bootstrap node or not', metavar='[True|False]')
@click.option('--nodes', required=True, help='Enter number of total nodes', metavar='<int>')
def register(port, bootstrap, nodes):

	"""\b
	-------------------------------------------
	This command creates a new node for noobcash
	blockchain.
	-------------------------------------------
	NOTE: The function returns the system's
	status for thic action("OK" on success / "failed"
	on failure).
	-------------------------------------------
	"""
	validation.valid_port(port)
	validation.valid_nodes(nodes)
	click.echo()
    
	with open('./temporary_file.txt', 'w') as temp:
		temp.write(nodes)
		temp.write('\n')
		temp.write(port)
	cmd = "python rest.py " + port + " " + str(int(nodes) - 1)  + " " + bootstrap
	os.system(cmd)	
	
	return   

    

@click.option('--receiver', required=True, help='Enter the id of receiver node', metavar='<int>')
@click.option('--amount', required=True, help = 'Enter the amount delivered from this transaction', metavar='<int>')   
@cli.command(short_help='Create a new transaction')
def t(receiver, amount):

	"""\b
	-------------------------------------------
	This command creates a new transaction sended from
	this node.
	-------------------------------------------
	NOTE: The function returns the system's
	status for thic action("OK" on success / "failed"
	on failure).
	-------------------------------------------
	"""

	with open('./temporary_file.txt', 'r') as temp:
		#print('LINESSSSSSSS', temp.readlines())
		lines = temp.readlines()
		nodes = int(lines[0][:-1])
		#print(nodes)
		port = int(lines[1])
	validation.valid_receiver(receiver, nodes)
	validation.valid_amount(amount)
	click.echo()
    
	receiver = str(int(receiver) - 1)
    
	response = requests.get('http://' + HOST_IP + ':' + str(port) + '/cli/get_id')
	text = json.loads(response.text)
	myid = text['id'] + 1

	data = {'receiver' : receiver, 'amount' : amount} 
	data = json.dumps(data)
	response = requests.post('http://' + HOST_IP + ':' + str(port) + '/cli/create_transaction', data = data)
	if response.status_code == 200:
		click.echo(click.style('Successful Transaction! ' + amount + ' NBCs transfered from node ' + str(myid) + ' to node ' + str(int(receiver) + 1), fg = 'green'))
	elif response.status_code == 400:
		click.echo(click.style('Error Transaction. Not enough money.', fg = 'red'))
	elif response.status_code == 404:
		click.echo(click.style('Error Transaction. Not valid receiver node.', fg = 'red'))
	return 


@cli.command(short_help='View transactions of last validated block of blockchain')
def view():

	"""\b
	-------------------------------------------
	This command shows transactions of last validated
	block of this node's blockchain.
	-------------------------------------------
	NOTE: The function returns the system's
	status for thic action("OK" on success / "failed"
	on failure).
	-------------------------------------------
	"""   
    
	with open('./temporary_file.txt') as temp:
		lines = temp.readlines()
		nodes = int(lines[0][:-1])	
		port = int(lines[1])

	response = requests.get('http://' + HOST_IP + ':' + str(port) + '/cli/view')
	text = json.loads(response.text)
	list_trans = text['listOfTransactions']
	for cnt, trans in enumerate(list_trans):
		print('TRANSACTION ' + str(cnt) + ':')
		print('Sender Address :' , trans['content']['sender_address'])
		print('Receiver Address :',  trans['content']['receiver_address'])
		print('Amount :' , trans['content']['amount'])
		print('Transaction Inputs List :', trans['content']['transaction_inputs'])
		print('Transaction Outputs List :', trans['content']['transaction_outputs'])
		print('Hash ID :', trans['hash_id'])
	return
   

@cli.command(short_help='View balcance of the wallet')
def balance():

	"""\b
	-------------------------------------------
	This command shows balance of this node's wallet.
	-------------------------------------------
	NOTE: The function returns the system's
	status for thic action("OK" on success / "failed"
	on failure).
	-------------------------------------------
	"""   
	with open('./temporary_file.txt') as temp:
		lines = temp.readlines()
		nodes = int(lines[0][:-1])
		port = int(lines[1])
	response = requests.get('http://' + HOST_IP + ':' + str(port) + '/cli/balance')
	amount = json.loads(response.text)['amount']
	print('MY BALANCE:', amount)
	return
