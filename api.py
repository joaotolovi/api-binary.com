import requests
import websocket
import time
from threading import Thread
import json
import datetime
import random

class Binary():
    payout_min=0;
    currency_char=''
    balance=0
    balance_actualy=''
    currency_char_types = {'BRL':'R$', 'USD':'$', 'EUR':'€'}


    def __init__(self,email,token):
        self.token=token
        self.email=email
        self.payout_min=0
        self.sock_on = True
        apiUrl = "wss://ws.binaryws.com/websockets/v3?app_id=23625"
        self.ws = websocket.WebSocketApp(apiUrl, on_message = self.on_message, on_open = self.on_open,on_error = self.on_error,on_close=self.on_socket_close)

    def on_error(self,error):
        print(error)

    def login(self):
        if self.ws.keep_running==True:self.ws.close()
        self.socket_thread = Thread(target=self.ws.run_forever).start()
        self.socket_message={}
        time.sleep(1)
        login=self.send_socket_message({"authorize": self.token})
        self.start_profile(login)
        if 'authorize' in login:
            if login['authorize']['email']==self.email:
                self.actives=self.get_all_actives()
                confset('binary','email',self.email)
                confset('binary','senha',self.token)
                self.sock_on = True
                return True
        return 'connection error'

    def start_profile(self,info):
        print(info)
        self.balance=info['authorize']['balance']
        self.currency_char=self.currency_char_types[info['authorize']['currency']]
        type_balance={1:'PRACTICE',0:'REAL'}
        self.balance_actualy=type_balance[info['authorize']['is_virtual']]
        self.logg=info['authorize']['email']
        self.send_socket_message({"balance": 1,"subscribe": 1})


    def change_balance(self,balance):
        return self.balance_actualy,self.balance

    def on_open(self):pass

    def on_socket_close(self):self.sock_on = False

    def on_message(self, message):
        self.socket_message=json.loads(message)
        if('balance' in self.socket_message):self.balance_changed(self.socket_message)

    def send_socket_message(self,message_send):
        request_id=random.randint(0, 5000)
        message_send.update({"req_id":request_id})
        self.ws.send(json.dumps(message_send))
        a=0
        while True:
            if "req_id" in self.socket_message:
                if self.socket_message["req_id"]==request_id:break
            if a>=30:return False
            a+=1
            time.sleep(0.1)
        return self.socket_message

    def balance_changed(self,balance_chage):
        self.balance=balance_chage['balance']['balance']


    def prebuy(self,price,active,direction,exp):
        price=float(price)
        exp=int(exp)
        contract=self.send_socket_message({"proposal": 1,"amount": price,"basis": "stake","contract_type": direction.upper(),"currency": "USD","duration": exp*60,"duration_unit": "s", "symbol": self.actives[active.upper()]})
        if 'proposal' in contract and 'id' in contract['proposal']:
            if (((contract['proposal']["payout"])/price)*100)>=self.payout_min:
                return 'bin',(((contract['proposal']["payout"])/price)*100),False,contract
            else:return "PayMin",(((contract['proposal']["payout"])/price)*100),False
        return [False]


    def buy(self,contract,price):
        buy=self.send_socket_message({"buy":contract['proposal']['id'], "price": price})
        return True,buy["buy"]["contract_id"]

    def get_optioninfo(self, size):
        return self.send_socket_message({"profit_table": 1,"description": 1,"limit": size})

    def check_win(self,idd, positions=[]):
        contract=self.send_socket_message({"proposal_open_contract": 1,"contract_id": idd})
        try:
            if contract['proposal_open_contract']['status']!="open":
                return {'profit':contract['proposal_open_contract']['profit']}
        except:pass
        return False

    def get_time(self):
        self.timeSync=self.send_socket_message({"time": 1})['time']

    def get_price_now(self,active):
        price=self.send_socket_message({"ticks_history": active,"count": 2,"end": "latest","start": 1,"style": "ticks"})
        return {'open':price['history']['prices'][0],'close':price['history']['prices'][1]}

    def check_connect(self):
        try:
            requests.get('https://www.binary.com/')
            return True
        except:
            return False

    def get_all_actives(self):
        activies=self.send_socket_message({"active_symbols": "brief","product_type": "basic"})
        symbols={}
        for x in activies["active_symbols"]:
            symbols.update({x["symbol"].replace('frx',''):x["symbol"]})
        return symbols

    def get_all_profit(self):
        '''pass'''

    def change_balance(self,balance):pass
    def get_balance(self):return self.balance
