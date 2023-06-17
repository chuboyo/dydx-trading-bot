from func_connections import connect_dydx
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from func_private import abort_all_positions
from func_public import construct_market_prices
from func_cointegration import store_cointegration_results
from func_entry_pairs import open_positions
from func_exit_pairs import manage_trade_exits
from func_messaging import send_message


send_message('bot is online')

try:
    client = connect_dydx()
except Exception as exc:
    print(exc)
    send_message('failed to connect to client')
    exit(1)

if ABORT_ALL_POSITIONS:
    try:
        print('closing all positions')
        close_orders = abort_all_positions(client)
    except Exception as exc:
        print(exc)
        send_message('error closing all positions')
        exit(1)

if FIND_COINTEGRATED:
    try:
        print('Fetching market data....')
        df_market_prices = construct_market_prices(client)
    except Exception as exc:
        print('Error fetching market data...')
        print(exc)
        send_message('error constructing market prices')
        exit(1)

    try:
        print('Storing cointegrated pairs....')
        stores_result = store_cointegration_results(df_market_prices)
        if stores_result != 'saved':
            print('error saving cointegrated pairs.....')
            exit(1)
    except Exception as exc:
        # print('i here')
        print('error saving cointegrated pairs', exc)
        send_message('error saving cointegrated pairs')
        exit(1)

while True:

    if MANAGE_EXITS:
        try:
            print('Managing exits....')
            manage_trade_exits(client)
        except Exception as exc:
            # print('i here')
            print('Error managing exiting positions...', exc)
            send_message('error managing exiting positions')
            exit(1)

    if PLACE_TRADES:
        try:
            print('Finding trading opportunities....')
            open_positions(client)
        except Exception as exc:
            # print('i here')
            print('Error trading pairs', exc)
            send_message('error opening trading')
            exit(1)

