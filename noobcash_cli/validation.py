import click
#import os.path
#import os

def valid_port(port):
    cnt = 0
    for ch in port:
        if not ch.isdigit():
            raise click.BadParameter("invalid format: " + port +  ". (valid format: XXXX, X = integer)", param = port, param_hint = "'--port'") 
        cnt += 1
    if not cnt == 4:
        raise click.BadParameter("invalid format: " + port + ". (valid format: XXXX, X = integer)", param = port, param_hint = "'--port'")
    return True
    
def valid_nodes(nodes):
    for ch in nodes:
        if not ch.isdigit():
            raise click.BadParameter("invalid type: " + nodes + ". (valid type: integer)", param = nodes, param_hint = "'--nodes'")    
    return True
    
    
def valid_receiver(receiver, nodes):
    for ch in receiver:
        if not ch.isdigit():
            raise click.BadParameter("invalid type: " + receiver + ". (valid type: integer)", param = receiver, param_hint = "'--receiver'")    
    if int(receiver) > int(nodes):
        raise click.BadParameter("invalid: " +  receiver + ". (valid: receiver number must be between 1 and " + str(nodes) + ")", param = receiver, param_hint = "'--receiver'")
    return True
    
def valid_amount(amount):
    for ch in amount:
        if not ch.isdigit():
            raise click.BadParameter("invalid type: " + amount + ". (valid type: integer)", param = amount, param_hint = "'--amount'") 
    return True
