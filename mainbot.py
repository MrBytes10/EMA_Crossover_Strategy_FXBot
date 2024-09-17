import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, time as dt_time
import time
import pytz
import logging
import os
from dotenv import load_dotenv

# Import config (if exists)
try:
    import config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SYMBOL = os.getenv('SYMBOL', 'EURUSD')
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 3))
RISK_PERCENT = float(os.getenv('RISK_PERCENT', 1))
STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 0.02))
TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', 0.04))
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'America/New_York'))

def initialize_mt5():
    """Initialize MetaTrader5 connection"""
    if not mt5.initialize():
        logger.warning("Failed to initialize MT5. Attempting to initialize with account details.")
        if HAS_CONFIG:
            if not mt5.initialize(**config.MT5_ACCOUNT):
                logger.error("Failed to initialize MT5 with account details.")
                return False
            logger.info("MT5 initialized successfully with account details.")
        else:
            logger.error("Failed to initialize MT5 and no config file found.")
            return False
    else:
        logger.info("MT5 initialized successfully.")
    return True

def calculate_ema(df, window):
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=window, adjust=False).mean()

def get_signals(df):
    """Generate buy/sell signals based on EMA crossover"""
    df['ema_50'] = calculate_ema(df, 50)
    df['ema_200'] = calculate_ema(df, 200)
    
    if df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1] and df['ema_50'].iloc[-2] <= df['ema_200'].iloc[-2]:
        return 'buy'
    elif df['ema_50'].iloc[-1] < df['ema_200'].iloc[-1] and df['ema_50'].iloc[-2] >= df['ema_200'].iloc[-2]:
        return 'sell'
    return None

def calculate_position_size(account_balance, risk_percent=RISK_PERCENT):
    """Calculate position size based on account balance and risk percentage"""
    return account_balance * (risk_percent / 100)

def set_stop_loss_and_take_profit(entry_price, direction, stop_loss_pct=STOP_LOSS_PERCENT, take_profit_pct=TAKE_PROFIT_PERCENT):
    """Set stop loss and take profit levels"""
    if direction == 'buy':
        sl = entry_price * (1 - stop_loss_pct)
        tp = entry_price * (1 + take_profit_pct)
    else:  # for 'sell' direction
        sl = entry_price * (1 + stop_loss_pct)
        tp = entry_price * (1 - take_profit_pct)
    return sl, tp

def trade(symbol, direction, account_balance):
    """Execute a trade"""
    try:
        lot_size = calculate_position_size(account_balance)
        price = mt5.symbol_info_tick(symbol).ask if direction == 'buy' else mt5.symbol_info_tick(symbol).bid
        sl, tp = set_stop_loss_and_take_profit(price, direction)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": mt5.ORDER_TYPE_BUY if direction == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": f"EMA {direction.capitalize()}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Trade execution failed. Error code: {result.retcode}")
            return None
        logger.info(f"Trade executed successfully: {result.comment}")
        return result
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return None

def max_open_positions(symbols, max_trades=MAX_POSITIONS):
    """Check if the maximum number of open positions has been reached"""
    positions = mt5.positions_get(symbols=symbols)
    return len(positions) < max_trades

def is_within_trading_hours():
    """Check if current time is within the specified trading hours"""
    now = datetime.now(TIMEZONE).time()
    start = dt_time(8, 0)  # 8:00 AM
    end = dt_time(12, 0)  # 12:00 PM
    return start <= now <= end

def check_major_news_events():
    """Check for major economic news releases"""
    # TODO: Implement API call to check for major economic news releases
    # For now, we'll assume there are no major news events
    logger.warning("News event checking not implemented. Assuming no major news.")
    return True

def get_rates(symbol, timeframe=mt5.TIMEFRAME_D1, number_of_data=200):
    """Fetch historical price data"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, number_of_data)
    if rates is None or len(rates) == 0:
        logger.error(f"Failed to fetch rates for {symbol}")
        return None
    rates_df = pd.DataFrame(rates)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
    return rates_df

def adjust_stop_loss(position):
    """Move stop-loss to break-even if profit reaches 2%"""
    if (position.profit / position.volume) >= (position.price_open * 0.02):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "sl": position.price_open
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to move stop-loss for position {position.ticket}. Error code: {result.retcode}")
        else:
            logger.info(f"Stop-loss moved to break-even for position {position.ticket}")

def main():
    if not initialize_mt5():
        return

    while True:
        try:
            if is_within_trading_hours():
                account_info = mt5.account_info()
                if account_info is None:
                    logger.error("Failed to get account info")
                    continue
                account_balance = account_info.balance

                if check_major_news_events():
                    rates_df = get_rates(SYMBOL)
                    if rates_df is not None:
                        signal = get_signals(rates_df)

                        if signal and max_open_positions([SYMBOL]):
                            trade(SYMBOL, signal, account_balance)

                # Re-evaluate positions and adjust stop-loss
                positions = mt5.positions_get(symbol=SYMBOL)
                for position in positions:
                    adjust_stop_loss(position)

            time.sleep(60 * 60 * 4)  # Re-check every 4 hours
        except Exception as e:
            logger.error(f"An error occurred in the main loop: {str(e)}")
            time.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
    finally:
        mt5.shutdown()
        logger.info("MT5 connection closed")