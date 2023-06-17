from constants import ZSCORE_THRESH, USD_PER_TRADE, USD_MIN_COLLATERAL, TOKEN_FACTOR_10
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_private import is_open_positions
from func_bot_agent import BotAgent
import pandas as pd
import json
from pprint import pprint


def open_positions(client):
    df = pd.read_csv('cointegrated_pairs.csv')
    # print(df)

    markets = client.public.get_markets().data

    bot_agents = []

    try:
        open_positions_file = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_file)

        for p in open_positions_dict:
            bot_agents.append(p)
    except:
        bot_agents = []

    

    for index, row in df.iterrows():
        base_market = row['base_market']
        quote_market = row['quote_market']
        hedge_ratio = row['hedge_ratio']
        half_life = row['half_life']

        series_1 = get_candles_recent(client, base_market)
        series_2 = get_candles_recent(client, quote_market)

        if len(series_1) > 0 and len(series_1) == len(series_2):
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1]
            
            if abs(z_score) >= ZSCORE_THRESH:
                is_base_open = is_open_positions(client, base_market)
                is_quote_open = is_open_positions(client, quote_market)

                if not is_base_open and not is_quote_open:
                    base_side = 'BUY' if z_score < 0 else 'SELL'
                    quote_side = 'SELL' if z_score < 0 else 'BUY'

                    base_price = series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99
                    accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99
                    failsafe_base_price = float(base_price) * 0.05 if z_score < 0 else float(base_price) * 1.7
                    quote_tick_size = markets['markets'][quote_market]['tickSize']
                    base_tick_size = markets['markets'][base_market]['tickSize']

                    accept_base_price = format_number(accept_base_price, base_tick_size)
                    accept_quote_price = format_number(accept_quote_price, quote_tick_size)
                    accept_failsafe_base_price = format_number(failsafe_base_price, base_tick_size)


                    base_quantity = 1/base_price * USD_PER_TRADE
                    quote_quantity = 1/quote_price * USD_PER_TRADE


                    for particolari in TOKEN_FACTOR_10 :
                        if base_market== particolari :
                            base_quantity= float(int(base_quantity/10)*10) 
                        if quote_market== particolari :
                            quote_quantity= float(int(quote_quantity/10)*10) 
                    base_step_size = markets['markets'][base_market]['stepSize']
                    quote_step_size = markets['markets'][base_market]['stepSize']

                    base_size = format_number(base_quantity, base_step_size)
                    quote_size = format_number(quote_quantity, quote_step_size)

                    base_min_order_size = markets['markets'][base_market]['minOrderSize']
                    quote_min_order_size = markets['markets'][quote_market]['minOrderSize']
                    check_base = float(base_quantity) > float(base_min_order_size)
                    check_quote = float(quote_quantity) > float(quote_min_order_size)

                    if check_base and check_quote:
                        account = client.private.get_account()
                        free_collateral = float(account.data['account']['freeCollateral'])
                        print(f'Balance: {free_collateral}, min: {USD_MIN_COLLATERAL}')

                        if free_collateral < USD_MIN_COLLATERAL:
                            break

                        bot_agent = BotAgent(
                            client,
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=accept_failsafe_base_price,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio,
                            z_score=z_score
                        )

                        bot_open_dict = bot_agent.open_trade()

                        if bot_open_dict['pair_status'] == 'LIVE':
                            bot_agents.append(bot_open_dict)
                            del bot_open_dict

                            print('Trade status live....')


    print(f'success {len(bot_agents)} pairs live')
    if len(bot_agents) > 0:
        with open('bot_agents.json', 'w') as f:
            json.dump(bot_agents, f)
        
