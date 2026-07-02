# Telegram Shop Bot

Telegram bot with:

- Main menu and product menu
- Admin panel through `/admin`
- Product stock/coupon management
- Binance Pay manual invoices with admin confirmation
- User balance, orders, and history
- English/French language switch

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BINANCE_PAY_ID=YOUR_BINANCE_PAY_ID
ADMIN_TELEGRAM_ID=YOUR_TELEGRAM_ID
```

Run:

```bash
python bot.py
```

## Notes

- Do not commit `.env`.
- `bot_data.json` stores local products, stock, balances, orders, and text overrides. It is ignored by Git. For hosted production, use persistent storage or a database.
- `/admin` works only for `ADMIN_TELEGRAM_ID`.
