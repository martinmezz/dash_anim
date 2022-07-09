from core.global_vars import *
import trello


clientTrello = trello.Lists(
    apikey = CONFIG['TRELLO']['APIKEY'],
    token = CONFIG['TRELLO']['TOKEN']
)

idList = '61550959926d8e171cb5351e'  # Help desk list ID

def new_issue(description=None):
    '''
    TODO: COMPLETAR DOCTRING
    '''

    return clientTrello.new_card(
        idList,
        "New Comment",
        None,
        description
    )
