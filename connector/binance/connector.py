# @date 2018-10-10
# @author Frederic SCHERMA
# @license Copyright (c) 2018 Dream Overflow
# HTTPS+WS connector for binance.com

from connector.binance.client import Client
from connector.binance.websockets import BinanceSocketManager

import logging
logger = logging.getLogger('siis.connector.binance')


class Connector(object):
	"""
	Binance adapter to REST and WS API.
	"""

	TF_MAP = {
		60: '1m',
		180: '3m',
		300: '5m',
		900: '15m',
		1800: '30m',
		3600: '1h',
		7200: '2h',
		14400: '4h',
		21600: '6h',
		28800: '8h',
		43200: '12h',
		86400: '1d',
		604800: '1w',
		2592000: '1M'
	}

	def __init__(self, service, account_id, api_key, api_secret, host="api.binance.com", callback=None):
		self._protocol = "https://"
		self._host = host or "api.binance.com"

		self._base_url = "/api/"  # for REST

		self._account_id = account_id

		self.__api_key = api_key
		self.__api_secret = api_secret

		self._session = None
		self._ws = None

	def connect(self, use_ws=True):
		if self._session is None:
			# Create HTTPS session
			self._session = Client(self.__api_key, self.__api_secret, None)

		if self._ws is None and use_ws:
			self._ws = BinanceSocketManager(self._session)

	def disconnect(self):
		if self._ws:
			self._ws.close()
			self._ws = None

			# but might be more general with a ref counter
			from twisted.internet import reactor
			try:
				reactor.stop()
			except:
				# if not running avoid exception
				pass

		if self._session:
			self._session = None

	@property
	def authenticated(self):
		return self.__api_key is not None

	@property
	def connected(self):
		return self._session is not None

	@property
	def ws_connected(self):
		return self._ws is not None

	@property
	def client(self):
		return self._session

	@property
	def ws(self):
		return self._ws

	@property
	def account_id(self):
		return self._account_id

	#
	# Conveniances helpers
	#

	def balances(self):
		"""
		Returns balances for any assets.
		"""
		if self._session:
			return self._session.get_account().get('balances', [])

		return []

	def balance_for(self, asset):
		"""
		Returns balance for a specific asset.
		"""
		if self._session:
			return self._session.get_asset_balance(asset)

		return []

	def deposits(self, asset=None, timestamp=None):
		"""
		Returns deposits for a specific asset or any.
		"""
		if self._session:
			data = {}
			if asset:
				data['asset'] = asset
			if timestamp:
				data['startTime'] = int(timestamp*1000)

			result = self._session.get_deposit_history(**data)

			if result and result.get('success'):
				return result.get('depositList', [])

		return []

	def withdraws(self, asset=None, timestamp=None):
		"""
		Returns withdraws for a specific asset or any.
		"""
		if self._session:
			data = {}
			if asset:
				data['asset'] = asset
			if timestamp:
				data['startTime'] = int(timestamp*1000)

			result = self._session.get_withdraw_history(**data)

			if result and result.get('success'):
				return result.get('withdrawList', [])

		return []

	def orders_for(self, symbol):
		"""
		Returns active orders for a specific symbol.
		"""
		if self._session:
			data = {'symbol': symbol}
			return self._session.get_open_orders(**data)

		return []

	def open_orders(self):
		if self._session:
			return self._session.get_open_orders()

		return []

	def trades_for(self, symbol, from_id=None, timestamp=None, limit=None):
		"""
		Get recent trade from timestamp or max possible (1000, default 500) for a specific instrument.
		"""
		if self._session:
			data = {'symbol': symbol}

			if from_id:
				data['fromId'] = from_id

			if timestamp:
				data['startTime'] = int(timestamp * 1000.0)

			if limit:
				data['limit'] = limit

			return self._session.get_my_trades(**data)

		return []

	def price_for_at(self, symbol, timestamp, tf=60):
		"""
		@param symbol Instrument pair symbol.
		@param timestamp Second based from timestamp.
		@param tf Mappable second based time frame.
		"""
		tf = 60*60
		mapped_tf = self.TF_MAP[tf]
		timestamp = int(timestamp / tf) * tf

		if self._session:
			return self._session.get_klines(symbol=symbol, interval=mapped_tf, startTime=int(timestamp*1000), endTime=int((timestamp+tf)*1000))

		return None

	def get_dust_log(self):
		"""
		Return an array with all past dust small amount balance conversions.
		"""
		if self._session:
			results = self._session.get_dust_log()
			if results.get('success'):
				results = results.get('results')
				if results and "rows" in results:
					return results.get('rows', [])

		return []

	def get_asset_details(self):
		"""
		Returns a dict of asset details (fee...).
		"""
		if self._session:
			results = self._session.get_asset_details()
			if results.get('success'):
				return results.get('assetDetail', {})

		return {}
