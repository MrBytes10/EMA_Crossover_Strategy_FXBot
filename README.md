# Forex Trading Bot

## Overview

This Forex Trading Bot is an automated trading system that uses the MetaTrader 5 (MT5) platform to execute trades based on a specific strategy. The bot is implemented in Python and uses the MetaTrader5 library for interaction with the trading platform.

## Strategy

The bot implements an Exponential Moving Average (EMA) crossover strategy with the following key components:

1. **EMA Crossover:**

   - Uses a 50-day EMA and a 200-day EMA.
   - Generates a buy signal when the 50-day EMA crosses above the 200-day EMA.
   - Generates a sell signal when the 50-day EMA crosses below the 200-day EMA.

2. **Risk Management:**

   - Stop-loss: Set at 2% below the entry price for buy orders, 2% above for sell orders.
   - Take-profit: Set at 4% above the entry price for buy orders, 4% below for sell orders.
   - Position sizing: 1% of account balance per trade.

3. **Trading Conditions:**

   - Only trades during specific hours: 8:00 AM to 12:00 PM EST (New York time).
   - Avoids trading during major news events (placeholder function, needs implementation).

4. **Position Management:**
   - Maximum of 3 open positions at any time.
   - Re-evaluates positions every 4 hours.
   - Moves stop-loss to break-even after a position reaches 2% profit.

## Setup

### Prerequisites

- Python 3.7 or higher
- MetaTrader 5 platform installed
- MetaTrader 5 account (demo or live)

### Installation

1. Clone this repository:

   ```
   git clone https://github.com/your-username/forex-trading-bot.git
   cd forex-trading-bot
   ```

2. Install required packages:

   ```
   pip install MetaTrader5 pandas numpy pytz python-dotenv
   ```

3. Create a `.env` file in the project root directory with the following content:

   ```
   SYMBOL=EURUSD
   MAX_POSITIONS=3
   RISK_PERCENT=1
   STOP_LOSS_PERCENT=0.02
   TAKE_PROFIT_PERCENT=0.04
   TIMEZONE=America/New_York
   ```

   Adjust these values as needed.

4. (Optional) Create a `config.py` file for MT5 account credentials:

   ```python
   MT5_ACCOUNT = {
       "login": 12345678,  # Replace with your account number
       "password": "your_password_here",  # Replace with your account password
       "server": "MetaQuotes-Demo",  # Replace with your broker's server
       "timeout": 60000
   }
   ```

   This file is used if MT5 fails to initialize without explicit login details.

5. Add `config.py` to your `.gitignore` file to prevent sensitive information from being uploaded to version control.

## Usage

Run the bot using the following command:

```
python forex_trading_bot.py
```

The bot will initialize, connect to MT5, and start trading based on the defined strategy.

## Customization

- Adjust the EMA periods, risk parameters, or trading hours by modifying the respective variables in the script or .env file.
- Implement the `check_major_news_events()` function to avoid trading during significant economic releases.
- Modify the `calculate_position_size()` function to implement a different position sizing strategy.

## Disclaimer

This bot is for educational purposes only. Trading forex carries a high level of risk and may not be suitable for all investors. Before using this bot with real money, thoroughly backtest the strategy and use it on a demo account. The authors are not responsible for any financial losses incurred from using this bot.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/your-username/forex-trading-bot/issues) if you want to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
