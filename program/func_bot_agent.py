from func_private import check_order_status, place_market_order
from func_messaging import send_message
from datetime import datetime, timedelta
import time 
from pprint import pprint

class BotAgent:
    def __init__(
            self,
            client,
            market_1, 
            market_2,
            base_side,
            base_size,
            base_price,
            quote_side,
            quote_size,
            quote_price,
            accept_failsafe_base_price,
            z_score,
            half_life,
            hedge_ratio
            ):
        self.client = client
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio

        self.order_dict = {
            'market_1': market_1,
            'market_2': market_2,
            'hedge_ratio': hedge_ratio,
            'z_score': z_score,
            'half_life': half_life,
            'order_id_m1': '',
            'order_m1_side': base_side,
            'order_m1_size': base_size,
            'order_time_m1': '',
            'order_id_m2': '',
            'order_m2_side': quote_side,
            'order_m2_size': quote_size,
            'order_time_m2':'',
            'pair_status': '',
            'comments': ''
        }

    def check_order_status_by_id(self, order_id):

            time.sleep(2)

            order_status = check_order_status(self.client, order_id)
            if order_status == 'CANCELED':
                print(f'{self.market_1} {self.market_2} - order canceled...')
                self.order_dict['pair_status'] = 'FAILED'
                return 'failed'
            
            if order_status != 'FAILED':
                time.sleep(15)
                order_status = check_order_status(self.client, order_id)

                if order_status == 'CANCELED':
                    print(f'{self.market_1} {self.market_2} - order canceled...')
                    self.order_dict['pair_status'] = 'FAILED'
                    return 'failed'
                
                if order_status != 'FILLED':
                    print(f'{self.market_1} {self.market_2} - order error...')
                    self.client.private.cancel_order(order_id)
                    self.order_dict['pair_status'] = 'ERROR'
                    return 'error'
                
            return 'live'
    

    def open_trade(self):
         print('---')
         print(f'{self.market_1} placing first order')
         print(f'Side: {self.base_side}, Size: {self.base_size}, Price: {self.base_price}')
         print('---')

         try:
              base_order = place_market_order(
                   self.client,
                   market=self.market_1,
                   side=self.base_side,
                   size=self.base_size,
                   price=self.base_price,
                   reduce_only=False
              )
              self.order_dict['order_id_m1'] = base_order['order']['id']
              self.order_dict['order_time_m1'] = datetime.now().isoformat()
         except Exception as exc:
              self.order_dict['pair_status'] = 'ERROR'
              self.order_dict['comments'] = f'Market1 {self.market_1} - {exc}'
              return self.order_dict
         
         order_status_m1 = self.check_order_status_by_id(self.order_dict['order_id_m1'])

         if order_status_m1 != 'live':
              self.order_dict['pair_status'] = 'ERROR'
              self.order_dict['comments'] = f'{self.market_1} failed to fill'
              return self.order_dict

         print('---')
         print(f'{self.market_2} placing first order')
         print(f'Side: {self.quote_side}, Size: {self.quote_size}, Price: {self.quote_price}')
         print('---')

         time.sleep(0.5)

         try:
              quote_order = place_market_order(
                   self.client,
                   market=self.market_2,
                   side=self.quote_side,
                   size=self.quote_size,
                   price=self.quote_price,
                   reduce_only=False
              )
              self.order_dict['order_id_m2'] = quote_order['order']['id']
              self.order_dict['order_time_m2'] = datetime.now().isoformat()
         except Exception as exc:
              self.order_dict['pair_status'] = 'ERROR'
              self.order_dict['comments'] = f'Market2 {self.market_2} - {exc}'
              return self.order_dict
         
         order_status_m2 = self.check_order_status_by_id(self.order_dict['order_id_m2'])
         time.sleep(0.5)

         if order_status_m2 != 'live':
            self.order_dict['pair_status'] = 'ERROR'
            self.order_dict['comments'] = f'{self.market_2} failed to fill'

            try:
                close_order = place_market_order(
                    self.client,
                    market=self.market_2,
                    side=self.quote_side,
                    size=self.base_size,
                    price=self.accept_failsafe_base_price,
                    reduce_only=True
                )
                time.sleep(2)
                order_status_close_order = check_order_status(self.client, close_order['order']['id'])
                if order_status_close_order != 'FILLED':
                    print('abort program')
                    print('unexpected error')
                    print(order_status_close_order)
                    
                    send_message('failed to execute.code pink')

                    exit(1)
            except Exception as exc:
                self.order_dict['pair_status'] = 'ERROR'
                self.order_dict['comments'] = f'Close Market1 {self.market_1} - {exc}'
                # return self.order_dict
                print('abort program')
                print('unexpected error')
                print(order_status_close_order)
                send_message('failed to execute. code red')

                exit(1)
         else:
              self.order_dict['pair_status'] = 'LIVE'
              return self.order_dict
                    
         
              
            

