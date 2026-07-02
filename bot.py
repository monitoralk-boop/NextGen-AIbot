import html
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, InvalidToken
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


ENV_FILE = Path(__file__).with_name(".env")
DATA_FILE = Path(__file__).with_name("bot_data.json")
DEFAULT_LANGUAGE = "en"
CURRENCY = "USD"
MIN_DEPOSIT_USDT = Decimal("1")
BINANCE_PAY_ID_PLACEHOLDER = "PUT_YOUR_BINANCE_PAY_ID_HERE"
ADMIN_ID_PLACEHOLDER = "PUT_YOUR_TELEGRAM_ID_HERE"
INVOICE_EXPIRE_MINUTES = 15

TEST_COUPONS = [
    "TEST-COUPON-001",
    "TEST-COUPON-002",
    "TEST-COUPON-003",
    "TEST-COUPON-004",
    "TEST-COUPON-005",
]

PRODUCTS = [
    {
        "id": "random_coupon",
        "icon": "\U0001f3ab",
        "price": "0.01",
        "type": "random_coupon",
        "name": {
            "en": "Random Coupon",
            "fr": "Coupon aleatoire",
        },
        "description": {
            "en": "Test product. The bot sends one random coupon automatically.",
            "fr": "Produit de test. Le bot envoie un coupon aleatoire automatiquement.",
        },
        "coupons": TEST_COUPONS,
    },
]

LANGUAGE_FLAGS = {
    "en": "\U0001f1ec\U0001f1e7",
    "fr": "\U0001f1eb\U0001f1f7",
}

LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
}

TEXT = {
    "en": {
        "welcome": "\U0001f525 Welcome to {bot_name}!\n\n"
        "\U0001f4a7 Your balance: ${balance}",
        "shop_btn": "\U0001f3af Shop",
        "topup_btn": "\U0001f4b0 Top-up Wallet",
        "settings_btn": "\u26a1 Settings",
        "support_btn": "\U0001f514 Support",
        "history_btn": "\U0001f536 History",
        "language_btn": "\U0001f310 Language",
        "channel_btn": "\U0001f4a7 Channel",
        "main_menu_btn": "\U0001f519 Main Menu",
        "home_btn": "\U0001f3e0 Home",
        "back_menu_btn": "\u2b05 Back to menu",
        "back_deposit_btn": "\u2b05 Back to Deposit",
        "back_product_btn": "\u2b05 Back to Product",
        "help_btn": "\U0001f198 Help",
        "binance_btn": "\U0001f7e1 Binance Pay",
        "change_language_btn": "\U0001f310 Change language",
        "change_currency_btn": "\U0001f4b1 Change currency",
        "shop": "\U0001f3af Shop\n\nChoose a product:",
        "buy_btn": "\U0001f4a7 Pay with balance",
        "pay_binance_btn": "\U0001f7e1 Pay with Binance",
        "back_shop_btn": "\u2b05 Back to Shop",
        "product_not_found": "Product not found.",
        "product_detail": "<b>{name}</b>\n\n"
        "{description}\n\n"
        "Price: <b>${price}</b>\n"
        "Stock: <b>{stock}</b>\n"
        "Your balance: <b>${balance}</b>\n\n"
        "Choose a payment method, then send how many coupons you need.",
        "product_detail_out_of_stock": "<b>{name}</b>\n\n"
        "{description}\n\n"
        "Price: <b>${price}</b>\n"
        "Stock: <b>0</b>\n\n"
        "This product is out of stock right now.\n"
        "Please wait until we have stock again.",
        "quantity_prompt": "<b>{name}</b>\n\n"
        "How many coupons do you need?\n"
        "Available stock: <b>{stock}</b>\n"
        "Unit price: <b>${price}</b>\n\n"
        "Send a number, example: <code>3</code>",
        "invalid_quantity": "Please send a valid quantity, example: 3.",
        "quantity_too_low": "Quantity must be at least 1.",
        "not_enough_stock": "Only {stock} coupons are available right now.",
        "insufficient_balance": "\u274c Not enough balance.\n\n"
        "Total price: <b>${price}</b>\n"
        "Your balance: <b>${balance}</b>\n\n"
        "Please top up your wallet first.",
        "purchase_success": "\u2705 Purchase completed!\n\n"
        "Order ID: <code>{order_id}</code>\n"
        "Product: <b>{name}</b>\n"
        "Quantity: <b>{quantity}</b>\n"
        "Total price: <b>${price}</b>\n"
        "New balance: <b>${balance}</b>\n\n"
        "Your coupon(s):\n"
        "<code>{delivery}</code>",
        "purchase_success_binance": "\u2705 Purchase completed!\n\n"
        "Order ID: <code>{order_id}</code>\n"
        "Product: <b>{name}</b>\n"
        "Quantity: <b>{quantity}</b>\n"
        "Total price: <b>${price}</b>\n"
        "Paid with: <b>Binance Pay</b>\n\n"
        "Your coupon(s):\n"
        "<code>{delivery}</code>",
        "product_unavailable": "This product is out of stock right now.\n\nPlease wait until we have stock again.",
        "support": "\U0001f514 Support\n\nContact support here.",
        "history_empty": "\U0001f536 History\n\nNo history yet.",
        "history_title": "\U0001f536 History",
        "history_order": "\U0001f6d2 <b>Order</b> <code>{order_id}</code>\n"
        "{product_name} x{quantity} - ${price}\n"
        "{created_at}",
        "history_deposit": "\U0001f4b0 <b>Deposit</b> <code>{invoice_id}</code>\n"
        "{amount} USDT - {status}\n"
        "{created_at}",
        "history_payment": "\U0001f7e1 <b>Product payment</b> <code>{invoice_id}</code>\n"
        "{product_name} x{quantity} - ${amount} - {status}\n"
        "{created_at}",
        "channel": "\U0001f4a7 Channel\n\nAdd your channel link here.",
        "not_ready": "This option is not ready yet.",
        "help": "Send /start to open the bot menu.",
        "deposit": "\U0001f4b0 Deposit\n\n"
        "\U0001f381 Bonus Tiers\n"
        "\u2514 $50 \u2192 +2%  \u00b7  get $51.00\n"
        "\u2514 $100 \u2192 +5%  \u00b7  get $105.00\n"
        "Bonus scales with bigger deposits.\n\n"
        "Pick a payment method below to get started.\n\n"
        "\u2014 Payment Methods \u2014",
        "binance_invoice": "<b>BINANCE PAY \u00b7 INVOICE</b>\n"
        "----------\n\n"
        "<code>{invoice_id}</code>\n\n"
        "<i>Amount</i>  {amount} <b>USDT</b>\n"
        "<i>Pay to</i>  <code>{pay_id}</code>\n\n"
        "<i>How to pay</i>\n"
        "1. Open Binance \u2192 Pay \u2192 Send.\n"
        "2. Recipient: paste the Binance Pay ID above.\n"
        "3. Send the <b>exact amount: {amount} USDT.</b>\n"
        "4. Copy your <b>Transaction ID</b> from Binance Pay \u2192 History.\n"
        "5. Send the <b>Transaction ID as your next message.</b>\n\n"
        "<i>Invoice expires in {minutes} minutes.</i>",
        "binance_id_missing": "Binance Pay ID is missing.\n\n"
        "Add this line to your .env file:\n"
        "BINANCE_PAY_ID=YOUR_BINANCE_PAY_ID",
        "enter_deposit_amount": "\U0001f7e1 Binance Pay\n\n"
        "Enter the amount you want to deposit.\n"
        "Minimum: $1 / 1 USDT\n\n"
        "Example: 10",
        "invalid_deposit_amount": "Please send a valid amount.\n\nExample: 10",
        "amount_too_low": "Minimum deposit is $1 / 1 USDT.",
        "invoice_expired": "This invoice expired. Please create a new Binance Pay invoice.",
        "transaction_received": "\u2705 Transaction ID received:\n"
        "<code>{transaction_id}</code>\n\n"
        "Your deposit is waiting for admin confirmation.",
        "payment_received": "\u2705 Transaction ID received:\n"
        "<code>{transaction_id}</code>\n\n"
        "Your product payment is waiting for admin confirmation.",
        "admin_not_configured": "\u26a0 Transaction ID received, but admin approval is not configured yet.\n\n"
        "Please contact support.",
        "payment_admin_not_configured": "\u26a0 Transaction ID received, but admin approval is not configured yet.\n\n"
        "Please contact support.",
        "deposit_confirmed": "\u2705 Deposit confirmed!\n\n"
        "Amount: <b>{amount} USDT</b>\n"
        "New balance: <b>${balance}</b>",
        "deposit_rejected": "\u274c Deposit rejected.\n\n"
        "Invoice: <code>{invoice_id}</code>\n"
        "Please contact support if this is a mistake.",
        "payment_rejected": "\u274c Product payment rejected.\n\n"
        "Invoice: <code>{invoice_id}</code>\n"
        "Please contact support if this is a mistake.",
        "deposit_help": "\U0001f198 Deposit Help\n\n"
        "Use Binance Pay, then send your Transaction ID to support.",
        "settings": "\u2699 Settings\n\n"
        "\U0001f310 Language: {language}\n"
        "Currency: {currency}",
        "language": "\U0001f310 Language\n\nChoose your language.",
        "language_changed": "Language changed to English.",
        "currency_soon": "Currency options coming soon.",
    },
    "fr": {
        "welcome": "\U0001f525 Bienvenue chez {bot_name} !\n\n"
        "\U0001f4a7 Votre solde : ${balance}",
        "shop_btn": "\U0001f3af Boutique",
        "topup_btn": "\U0001f4b0 D\u00e9p\u00f4t",
        "settings_btn": "\u26a1 Param\u00e8tres",
        "support_btn": "\U0001f514 Support",
        "history_btn": "\U0001f536 Historique",
        "language_btn": "\U0001f310 Langue",
        "channel_btn": "\U0001f4a7 Canal",
        "main_menu_btn": "\U0001f519 Menu principal",
        "home_btn": "\U0001f3e0 Accueil",
        "back_menu_btn": "\u2b05 Retour au menu",
        "back_deposit_btn": "\u2b05 Retour au d\u00e9p\u00f4t",
        "back_product_btn": "\u2b05 Retour au produit",
        "help_btn": "\U0001f198 Aide",
        "binance_btn": "\U0001f7e1 Binance Pay",
        "change_language_btn": "\U0001f310 Changer la langue",
        "change_currency_btn": "\U0001f4b1 Changer la devise",
        "shop": "\U0001f3af Boutique\n\nChoisissez un produit :",
        "buy_btn": "\U0001f4a7 Payer avec solde",
        "pay_binance_btn": "\U0001f7e1 Payer avec Binance",
        "back_shop_btn": "\u2b05 Retour a la boutique",
        "product_not_found": "Produit introuvable.",
        "product_detail": "<b>{name}</b>\n\n"
        "{description}\n\n"
        "Prix : <b>${price}</b>\n"
        "Stock : <b>{stock}</b>\n"
        "Votre solde : <b>${balance}</b>\n\n"
        "Choisissez une methode de paiement, puis envoyez la quantite voulue.",
        "product_detail_out_of_stock": "<b>{name}</b>\n\n"
        "{description}\n\n"
        "Prix : <b>${price}</b>\n"
        "Stock : <b>0</b>\n\n"
        "Ce produit est en rupture de stock pour le moment.\n"
        "Veuillez attendre le retour du stock.",
        "quantity_prompt": "<b>{name}</b>\n\n"
        "Combien de coupons voulez-vous ?\n"
        "Stock disponible : <b>{stock}</b>\n"
        "Prix unitaire : <b>${price}</b>\n\n"
        "Envoyez un nombre, exemple : <code>3</code>",
        "invalid_quantity": "Envoyez une quantite valide, exemple : 3.",
        "quantity_too_low": "La quantite doit etre au moins 1.",
        "not_enough_stock": "Il reste seulement {stock} coupons disponibles.",
        "insufficient_balance": "\u274c Solde insuffisant.\n\n"
        "Prix total : <b>${price}</b>\n"
        "Votre solde : <b>${balance}</b>\n\n"
        "Rechargez votre wallet d'abord.",
        "purchase_success": "\u2705 Achat termine !\n\n"
        "ID commande : <code>{order_id}</code>\n"
        "Produit : <b>{name}</b>\n"
        "Quantite : <b>{quantity}</b>\n"
        "Prix total : <b>${price}</b>\n"
        "Nouveau solde : <b>${balance}</b>\n\n"
        "Vos coupon(s) :\n"
        "<code>{delivery}</code>",
        "purchase_success_binance": "\u2705 Achat termine !\n\n"
        "ID commande : <code>{order_id}</code>\n"
        "Produit : <b>{name}</b>\n"
        "Quantite : <b>{quantity}</b>\n"
        "Prix total : <b>${price}</b>\n"
        "Paiement : <b>Binance Pay</b>\n\n"
        "Vos coupon(s) :\n"
        "<code>{delivery}</code>",
        "product_unavailable": "Ce produit est en rupture de stock pour le moment.\n\nVeuillez attendre le retour du stock.",
        "support": "\U0001f514 Support\n\nContactez le support ici.",
        "history_empty": "\U0001f536 Historique\n\nAucun historique pour le moment.",
        "history_title": "\U0001f536 Historique",
        "history_order": "\U0001f6d2 <b>Commande</b> <code>{order_id}</code>\n"
        "{product_name} x{quantity} - ${price}\n"
        "{created_at}",
        "history_deposit": "\U0001f4b0 <b>D\u00e9p\u00f4t</b> <code>{invoice_id}</code>\n"
        "{amount} USDT - {status}\n"
        "{created_at}",
        "history_payment": "\U0001f7e1 <b>Paiement produit</b> <code>{invoice_id}</code>\n"
        "{product_name} x{quantity} - ${amount} - {status}\n"
        "{created_at}",
        "channel": "\U0001f4a7 Canal\n\nAjoutez le lien de votre canal ici.",
        "not_ready": "Cette option n'est pas encore pr\u00eate.",
        "help": "Envoyez /start pour ouvrir le menu du bot.",
        "deposit": "\U0001f4b0 D\u00e9p\u00f4t\n\n"
        "\U0001f381 Bonus\n"
        "\u2514 $50 \u2192 +2%  \u00b7  recevez $51.00\n"
        "\u2514 $100 \u2192 +5%  \u00b7  recevez $105.00\n"
        "Le bonus augmente avec le montant du d\u00e9p\u00f4t.\n\n"
        "Choisissez une m\u00e9thode de paiement pour commencer.\n\n"
        "\u2014 M\u00e9thodes de paiement \u2014",
        "binance_invoice": "<b>BINANCE PAY \u00b7 FACTURE</b>\n"
        "----------\n\n"
        "<code>{invoice_id}</code>\n\n"
        "<i>Montant</i>  {amount} <b>USDT</b>\n"
        "<i>Payer \u00e0</i>  <code>{pay_id}</code>\n\n"
        "<i>Comment payer</i>\n"
        "1. Ouvrez Binance \u2192 Pay \u2192 Send.\n"
        "2. Destinataire : collez l'ID Binance Pay ci-dessus.\n"
        "3. Envoyez le <b>montant exact : {amount} USDT.</b>\n"
        "4. Copiez votre <b>ID de transaction</b> depuis Binance Pay \u2192 History.\n"
        "5. Envoyez l'<b>ID de transaction comme prochain message.</b>\n\n"
        "<i>La facture expire dans {minutes} minutes.</i>",
        "binance_id_missing": "L'ID Binance Pay est manquant.\n\n"
        "Ajoutez cette ligne dans votre fichier .env :\n"
        "BINANCE_PAY_ID=VOTRE_ID_BINANCE_PAY",
        "enter_deposit_amount": "\U0001f7e1 Binance Pay\n\n"
        "Entrez le montant que vous voulez d\u00e9poser.\n"
        "Minimum : $1 / 1 USDT\n\n"
        "Exemple : 10",
        "invalid_deposit_amount": "Envoyez un montant valide.\n\nExemple : 10",
        "amount_too_low": "Le d\u00e9p\u00f4t minimum est $1 / 1 USDT.",
        "invoice_expired": "Cette facture a expir\u00e9. Cr\u00e9ez une nouvelle facture Binance Pay.",
        "transaction_received": "\u2705 ID de transaction re\u00e7u :\n"
        "<code>{transaction_id}</code>\n\n"
        "Votre d\u00e9p\u00f4t attend la confirmation de l'admin.",
        "payment_received": "\u2705 ID de transaction re\u00e7u :\n"
        "<code>{transaction_id}</code>\n\n"
        "Votre paiement produit attend la confirmation de l'admin.",
        "admin_not_configured": "\u26a0 ID de transaction re\u00e7u, mais la confirmation admin n'est pas encore configur\u00e9e.\n\n"
        "Contactez le support.",
        "payment_admin_not_configured": "\u26a0 ID de transaction re\u00e7u, mais la confirmation admin n'est pas encore configur\u00e9e.\n\n"
        "Contactez le support.",
        "deposit_confirmed": "\u2705 D\u00e9p\u00f4t confirm\u00e9 !\n\n"
        "Montant : <b>{amount} USDT</b>\n"
        "Nouveau solde : <b>${balance}</b>",
        "deposit_rejected": "\u274c D\u00e9p\u00f4t refus\u00e9.\n\n"
        "Facture : <code>{invoice_id}</code>\n"
        "Contactez le support si c'est une erreur.",
        "payment_rejected": "\u274c Paiement produit refus\u00e9.\n\n"
        "Facture : <code>{invoice_id}</code>\n"
        "Contactez le support si c'est une erreur.",
        "deposit_help": "\U0001f198 Aide au d\u00e9p\u00f4t\n\n"
        "Utilisez Binance Pay, puis envoyez votre ID de transaction au support.",
        "settings": "\u2699 Param\u00e8tres\n\n"
        "\U0001f310 Langue : {language}\n"
        "Devise : {currency}",
        "language": "\U0001f310 Langue\n\nChoisissez votre langue.",
        "language_changed": "Langue chang\u00e9e en fran\u00e7ais.",
        "currency_soon": "Les options de devise arrivent bient\u00f4t.",
    },
}


def load_env_file() -> None:
    """Load simple KEY=VALUE lines from .env without requiring extra packages."""
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_token() -> str:
    load_env_file()
    token = os.getenv("BOT_TOKEN", "").strip()

    if not token or token == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN is missing. Create a .env file next to bot.py with:\n"
            "BOT_TOKEN=123456789:YOUR_REAL_TOKEN_FROM_BOTFATHER"
        )

    return token


def get_binance_pay_id() -> str:
    load_env_file()
    return os.getenv("BINANCE_PAY_ID", "").strip()


def get_admin_id() -> int | None:
    load_env_file()
    raw_admin_id = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
    if not raw_admin_id or raw_admin_id == ADMIN_ID_PLACEHOLDER:
        return None

    try:
        return int(raw_admin_id)
    except ValueError:
        return None


def is_admin(user_id: int | None) -> bool:
    admin_id = get_admin_id()
    return admin_id is not None and user_id == admin_id


def get_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    language = context.user_data.get("language", DEFAULT_LANGUAGE)
    if language not in TEXT:
        return DEFAULT_LANGUAGE
    return language


def set_language(context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
    context.user_data["language"] = language if language in TEXT else DEFAULT_LANGUAGE


def tr(lang: str, key: str, **kwargs: str) -> str:
    data = load_db()
    template = (
        data.get("text_overrides", {})
        .get(lang, {})
        .get(key, TEXT.get(lang, TEXT[DEFAULT_LANGUAGE])[key])
    )
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        fallback = TEXT.get(lang, TEXT[DEFAULT_LANGUAGE])[key]
        return fallback.format(**kwargs)


def default_products() -> list[dict]:
    return json.loads(json.dumps(PRODUCTS))


def normalize_product(product: dict) -> dict:
    product.setdefault("type", "coupon")
    if product.get("id") == "random_coupon" and "coupons" not in product:
        product["coupons"] = TEST_COUPONS.copy()
    elif product.get("type") in {"coupon", "random_coupon"}:
        product.setdefault("coupons", [])
    return product


def normalize_products(products: list[dict]) -> list[dict]:
    return [normalize_product(product) for product in products if isinstance(product, dict)]


def default_db() -> dict:
    return {
        "users": {},
        "pending_deposits": {},
        "orders": {},
        "products": default_products(),
        "text_overrides": {},
        "support_contacts": [],
    }


def load_db() -> dict:
    if not DATA_FILE.exists():
        return default_db()

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_db()

    if not isinstance(data, dict):
        return default_db()

    data.setdefault("users", {})
    data.setdefault("pending_deposits", {})
    data.setdefault("orders", {})
    data.setdefault("products", default_products())
    data["products"] = normalize_products(data["products"])
    data.setdefault("text_overrides", {})
    data.setdefault("support_contacts", [])
    return data


def save_db(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_products() -> list[dict]:
    data = load_db()
    products = data.get("products") or default_products()
    if not isinstance(products, list):
        return default_products()
    normalized_products = normalize_products(products)
    if normalized_products != products:
        data["products"] = normalized_products
        save_db(data)
    return normalized_products


def save_products(products: list[dict]) -> None:
    data = load_db()
    data["products"] = products
    save_db(data)


def get_support_contacts() -> list[str]:
    data = load_db()
    contacts = data.get("support_contacts", [])
    if not isinstance(contacts, list):
        return []
    return [str(contact) for contact in contacts if str(contact).strip()]


def save_support_contacts(contacts: list[str]) -> None:
    data = load_db()
    data["support_contacts"] = contacts
    save_db(data)


def support_text(language: str) -> str:
    contacts = get_support_contacts()
    if not contacts:
        return TEXT.get(language, TEXT[DEFAULT_LANGUAGE])["support"]

    title = "\U0001f514 Support"
    intro = "Contact us:" if language == "en" else "Contactez-nous :"
    contact_lines = "\n".join(f"- {contact}" for contact in contacts)
    return f"{title}\n\n{intro}\n{contact_lines}"


def clear_admin_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("admin_flow", None)
    context.user_data.pop("admin_product_draft", None)
    context.user_data.pop("admin_stock_product_id", None)
    context.user_data.pop("admin_text_lang", None)
    context.user_data.pop("admin_text_key", None)


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("\u2795 Add product", callback_data="admin_add_product")],
            [InlineKeyboardButton("\U0001f4e6 Products", callback_data="admin_products")],
            [InlineKeyboardButton("\U0001f514 Support contacts", callback_data="admin_support_contacts")],
            [InlineKeyboardButton("\U0001f4a7 Edit Channel", callback_data="admin_edit_direct:channel")],
            [InlineKeyboardButton("\u270f Edit text", callback_data="admin_edit_text")],
            [
                InlineKeyboardButton(
                    "\U0001f504 Reset products", callback_data="admin_reset_products"
                )
            ],
            [
                InlineKeyboardButton(
                    "\U0001f504 Reset text", callback_data="admin_reset_text"
                )
            ],
            [InlineKeyboardButton("\u274c Cancel", callback_data="admin_cancel")],
        ]
    )


def admin_support_contacts_menu() -> InlineKeyboardMarkup:
    contacts = get_support_contacts()
    keyboard = [
        [InlineKeyboardButton("\u2795 Add contact", callback_data="admin_add_support_contact")]
    ]
    for index, contact in enumerate(contacts):
        label = f"\U0001f5d1 {contact}"
        keyboard.append(
            [InlineKeyboardButton(label[:64], callback_data=f"admin_delete_support:{index}")]
        )
    keyboard.append([InlineKeyboardButton("\u2b05 Admin panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)


def admin_support_contacts_text() -> str:
    contacts = get_support_contacts()
    if not contacts:
        return "\U0001f514 Support contacts\n\nNo contacts yet."

    lines = "\n".join(f"{index + 1}. {contact}" for index, contact in enumerate(contacts))
    return f"\U0001f514 Support contacts\n\n{lines}"


def admin_products_menu() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("\u2795 Add product", callback_data="admin_add_product")]]
    for product in get_products():
        label = f"\U0001f4e6 {product_button_text(product, DEFAULT_LANGUAGE)}"
        keyboard.append(
            [InlineKeyboardButton(label[:64], callback_data=f"admin_product:{product['id']}")]
        )
    keyboard.append([InlineKeyboardButton("\u2b05 Admin panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)


def admin_product_text(product: dict) -> str:
    return (
        "<b>Product</b>\n\n"
        f"ID: <code>{html.escape(product['id'])}</code>\n"
        f"Name: <b>{html.escape(product_name(product, DEFAULT_LANGUAGE))}</b>\n"
        f"Price: <b>${html.escape(product['price'])}</b>\n"
        f"Stock: <b>{product_stock_count(product)}</b>"
    )


def admin_product_menu(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("\u2795 Add stock", callback_data=f"admin_add_stock:{product_id}")],
            [InlineKeyboardButton("\U0001f5d1 Delete product", callback_data=f"admin_delete_product:{product_id}")],
            [InlineKeyboardButton("\u2b05 Products", callback_data="admin_products")],
        ]
    )


def admin_text_language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("\U0001f1ec\U0001f1e7 English", callback_data="admin_text_lang:en")],
            [InlineKeyboardButton("\U0001f1eb\U0001f1f7 French", callback_data="admin_text_lang:fr")],
            [InlineKeyboardButton("\u2b05 Admin panel", callback_data="admin_panel")],
        ]
    )


def admin_direct_text_language_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "\U0001f1ec\U0001f1e7 English",
                    callback_data=f"admin_direct_text_lang:{key}:en",
                )
            ],
            [
                InlineKeyboardButton(
                    "\U0001f1eb\U0001f1f7 French",
                    callback_data=f"admin_direct_text_lang:{key}:fr",
                )
            ],
            [InlineKeyboardButton("\u2b05 Admin panel", callback_data="admin_panel")],
        ]
    )


def admin_text_label(key: str) -> str:
    return "Support" if key == "support" else "Channel" if key == "channel" else key


def editable_text_keys(language: str) -> list[str]:
    return sorted(
        key for key in TEXT.get(language, TEXT[DEFAULT_LANGUAGE]).keys() if key != "support"
    )


def admin_text_key_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(key, callback_data=f"admin_text_key:{language}:{key}")]
        for key in editable_text_keys(language)
    ]
    keyboard.append([InlineKeyboardButton("\u2b05 Language", callback_data="admin_edit_text")])
    return InlineKeyboardMarkup(keyboard)


def make_product_id() -> str:
    return f"prod_{secrets.token_hex(4)}"


def parse_coupon_list(raw_text: str) -> list[str]:
    normalized = raw_text.replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def ensure_user(data: dict, user_id: int | str) -> dict:
    users = data.setdefault("users", {})
    user = users.setdefault(str(user_id), {"balance": "0.00"})
    user.setdefault("balance", "0.00")
    return user


def get_user_balance(user_id: int | str) -> str:
    data = load_db()
    user = ensure_user(data, user_id)
    save_db(data)
    return user["balance"]


def add_user_balance(data: dict, user_id: int | str, amount: Decimal) -> str:
    user = ensure_user(data, user_id)
    current_balance = Decimal(user.get("balance", "0.00"))
    new_balance = current_balance + amount
    user["balance"] = format_balance(new_balance)
    return user["balance"]


def subtract_user_balance(data: dict, user_id: int | str, amount: Decimal) -> str | None:
    user = ensure_user(data, user_id)
    current_balance = Decimal(user.get("balance", "0.00"))
    if current_balance < amount:
        return None

    new_balance = current_balance - amount
    user["balance"] = format_balance(new_balance)
    return user["balance"]


def create_order_id() -> str:
    return f"ORD-{secrets.token_hex(6).upper()}"


def find_product(product_id: str) -> dict | None:
    return next(
        (product for product in get_products() if product["id"] == product_id), None
    )


def find_product_in_data(data: dict, product_id: str) -> dict | None:
    products = normalize_products(data.setdefault("products", default_products()))
    data["products"] = products
    return next((product for product in products if product.get("id") == product_id), None)


def product_name(product: dict, language: str) -> str:
    return product["name"].get(language) or product["name"][DEFAULT_LANGUAGE]


def product_description(product: dict, language: str) -> str:
    return product["description"].get(language) or product["description"][DEFAULT_LANGUAGE]


def product_stock_count(product: dict) -> int:
    coupons = product.get("coupons") or []
    return len(coupons)


def product_button_text(product: dict, language: str) -> str:
    return (
        f"{product['icon']} {product_name(product, language)} "
        f"- ${product['price']} ({product_stock_count(product)} stock)"
    )


def consume_product_delivery(
    data: dict, product_id: str, quantity: int
) -> tuple[dict | None, list[str] | None]:
    products = normalize_products(data.setdefault("products", default_products()))
    data["products"] = products

    for product in products:
        if product.get("id") != product_id:
            continue

        coupons = product.get("coupons") or []
        if quantity <= 0 or len(coupons) < quantity:
            return product, None

        delivery = []
        for _ in range(quantity):
            index = secrets.randbelow(len(coupons))
            delivery.append(coupons.pop(index))

        product["coupons"] = coupons
        return product, delivery

    return None, None


def save_order(order: dict) -> None:
    data = load_db()
    data.setdefault("orders", {})[order["order_id"]] = order
    save_db(data)


def save_pending_deposit(deposit: dict) -> None:
    data = load_db()
    data.setdefault("pending_deposits", {})[deposit["invoice_id"]] = deposit
    ensure_user(data, deposit["user_id"])
    save_db(data)


def admin_deposit_menu(invoice_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "\u2705 Confirm", callback_data=f"admin_confirm:{invoice_id}"
                ),
                InlineKeyboardButton(
                    "\u274c Reject", callback_data=f"admin_reject:{invoice_id}"
                ),
            ]
        ]
    )


def admin_deposit_text(deposit: dict) -> str:
    user_id = str(deposit["user_id"])
    full_name = html.escape(deposit.get("full_name") or user_id)
    username = deposit.get("username")
    username_line = f"@{html.escape(username)}" if username else "-"
    purpose = deposit.get("purpose", "topup")
    title = (
        "Product payment waiting confirmation"
        if purpose == "purchase"
        else "Deposit waiting confirmation"
    )
    product_line = ""
    if purpose == "purchase":
        product_line = (
            f"Product: <b>{html.escape(str(deposit.get('product_name', '-')))}</b>\n"
            f"Quantity: <b>{html.escape(str(deposit.get('quantity', '1')))}</b>\n"
        )

    return (
        f"<b>{title}</b>\n\n"
        f"Invoice: <code>{html.escape(deposit['invoice_id'])}</code>\n"
        f"Amount: <b>{html.escape(deposit['amount'])} USDT</b>\n"
        f"{product_line}"
        f"Transaction ID: <code>{html.escape(deposit['transaction_id'])}</code>\n\n"
        f"User: <a href=\"tg://user?id={html.escape(user_id)}\">{full_name}</a>\n"
        f"Username: {username_line}\n"
        f"User ID: <code>{html.escape(user_id)}</code>"
    )


async def notify_admin_deposit(
    context: ContextTypes.DEFAULT_TYPE, deposit: dict
) -> bool:
    admin_id = get_admin_id()
    if admin_id is None:
        return False

    await context.bot.send_message(
        chat_id=admin_id,
        text=admin_deposit_text(deposit),
        reply_markup=admin_deposit_menu(deposit["invoice_id"]),
        parse_mode="HTML",
    )
    return True


def clear_invoice_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_deposit_amount", None)
    context.user_data.pop("awaiting_purchase_quantity", None)
    context.user_data.pop("awaiting_transaction_id", None)
    context.user_data.pop("deposit_amount", None)
    context.user_data.pop("payment_purpose", None)
    context.user_data.pop("purchase_payment_method", None)
    context.user_data.pop("product_id", None)
    context.user_data.pop("product_name", None)
    context.user_data.pop("product_quantity", None)
    context.user_data.pop("unit_price", None)
    context.user_data.pop("invoice_id", None)
    context.user_data.pop("invoice_expires_at", None)


def create_invoice_id() -> str:
    return f"TOP-{secrets.token_hex(8).upper()}"


def parse_deposit_amount(raw_amount: str) -> Decimal | None:
    cleaned = (
        raw_amount.upper()
        .replace("USDT", "")
        .replace("USD", "")
        .replace("$", "")
        .replace(",", ".")
        .strip()
    )

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None

    if not amount.is_finite():
        return None

    return amount


def format_deposit_amount(amount: Decimal) -> str:
    normalized = amount.normalize()
    if normalized == normalized.to_integral():
        return format(normalized.quantize(Decimal("1")), "f")
    return format(normalized, "f")


def format_balance(amount: Decimal) -> str:
    return format(amount.quantize(Decimal("0.01")), "f")


def parse_quantity(raw_quantity: str) -> int | None:
    try:
        quantity = int(raw_quantity.strip())
    except ValueError:
        return None

    if quantity < 1:
        return None
    return quantity


def product_total_price(product: dict, quantity: int) -> Decimal:
    return Decimal(product["price"]) * Decimal(quantity)


def format_delivery(coupons: list[str]) -> str:
    return "\n".join(coupons)


def format_timestamp(value: str | None) -> str:
    if not value:
        return "-"

    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return value

    return timestamp.strftime("%Y-%m-%d %H:%M UTC")


def history_text(user_id: int | str, language: str) -> str:
    data = load_db()
    user_id_text = str(user_id)
    entries = []

    for deposit in data.get("pending_deposits", {}).values():
        if str(deposit.get("user_id")) != user_id_text:
            continue

        if deposit.get("purpose") == "purchase":
            entry_text = tr(
                language,
                "history_payment",
                    invoice_id=html.escape(str(deposit.get("invoice_id", "-"))),
                    product_name=html.escape(str(deposit.get("product_name", "-"))),
                    quantity=html.escape(str(deposit.get("quantity", "1"))),
                    amount=html.escape(str(deposit.get("amount", "0"))),
                    status=html.escape(str(deposit.get("status", "pending"))),
                    created_at=html.escape(format_timestamp(deposit.get("created_at"))),
            )
        else:
            entry_text = tr(
                language,
                "history_deposit",
                invoice_id=html.escape(str(deposit.get("invoice_id", "-"))),
                amount=html.escape(str(deposit.get("amount", "0"))),
                status=html.escape(str(deposit.get("status", "pending"))),
                created_at=html.escape(format_timestamp(deposit.get("created_at"))),
            )

        entries.append(
            {
                "created_at": deposit.get("created_at", ""),
                "text": entry_text,
            }
        )

    for order in data.get("orders", {}).values():
        if str(order.get("user_id")) != user_id_text:
            continue

        entries.append(
            {
                "created_at": order.get("created_at", ""),
                "text": tr(
                    language,
                    "history_order",
                    order_id=html.escape(str(order.get("order_id", "-"))),
                    product_name=html.escape(str(order.get("product_name", "-"))),
                    quantity=html.escape(str(order.get("quantity", "1"))),
                    price=html.escape(str(order.get("price", "0"))),
                    created_at=html.escape(format_timestamp(order.get("created_at"))),
                ),
            }
        )

    if not entries:
        return tr(language, "history_empty")

    entries.sort(key=lambda item: item["created_at"], reverse=True)
    recent_entries = entries[:10]
    return tr(language, "history_title") + "\n\n" + "\n\n".join(
        entry["text"] for entry in recent_entries
    )


def binance_invoice_text(
    language: str, invoice_id: str, pay_id: str, amount: str
) -> str:
    return tr(
        language,
        "binance_invoice",
        invoice_id=html.escape(invoice_id),
        amount=html.escape(amount),
        pay_id=html.escape(pay_id),
        minutes=str(INVOICE_EXPIRE_MINUTES),
    )


def language_label(language: str) -> str:
    flag = LANGUAGE_FLAGS.get(language, LANGUAGE_FLAGS[DEFAULT_LANGUAGE])
    name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    return f"{flag} {name}"


def welcome_text(language: str, bot_name: str, balance: str) -> str:
    return tr(language, "welcome", bot_name=bot_name, balance=balance)


async def get_bot_name(context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = await context.bot.get_me()
    return bot.first_name or bot.username or "Bot"


def main_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(tr(language, "shop_btn"), callback_data="shop")],
        [
            InlineKeyboardButton(tr(language, "topup_btn"), callback_data="topup"),
            InlineKeyboardButton(tr(language, "settings_btn"), callback_data="settings"),
        ],
        [
            InlineKeyboardButton(tr(language, "support_btn"), callback_data="support"),
            InlineKeyboardButton(tr(language, "history_btn"), callback_data="history"),
        ],
        [
            InlineKeyboardButton(tr(language, "language_btn"), callback_data="language"),
            InlineKeyboardButton(tr(language, "channel_btn"), callback_data="channel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(tr(language, "back_menu_btn"), callback_data="menu")]]
    )


def shop_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(product_button_text(product, language), callback_data=f"product:{product['id']}")]
        for product in get_products()
    ]
    keyboard.append([InlineKeyboardButton(tr(language, "home_btn"), callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)


def product_menu(language: str, product_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(tr(language, "buy_btn"), callback_data=f"buy:{product_id}")],
        [
            InlineKeyboardButton(
                tr(language, "pay_binance_btn"),
                callback_data=f"pay_product_binance:{product_id}",
            )
        ],
        [
            InlineKeyboardButton(tr(language, "back_shop_btn"), callback_data="shop"),
            InlineKeyboardButton(tr(language, "home_btn"), callback_data="menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def out_of_stock_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(tr(language, "back_shop_btn"), callback_data="shop"),
            InlineKeyboardButton(tr(language, "home_btn"), callback_data="menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def product_payment_back_menu(language: str, product_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                tr(language, "back_product_btn"), callback_data=f"product:{product_id}"
            )
        ],
        [InlineKeyboardButton(tr(language, "main_menu_btn"), callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def product_text(product: dict, language: str, balance: str) -> str:
    if product_stock_count(product) <= 0:
        return tr(
            language,
            "product_detail_out_of_stock",
            name=html.escape(product_name(product, language)),
            description=html.escape(product_description(product, language)),
            price=html.escape(product["price"]),
        )

    return tr(
        language,
        "product_detail",
        name=html.escape(product_name(product, language)),
        description=html.escape(product_description(product, language)),
        price=html.escape(product["price"]),
        stock=html.escape(str(product_stock_count(product))),
        balance=html.escape(balance),
    )


def quantity_prompt_text(product: dict, language: str) -> str:
    return tr(
        language,
        "quantity_prompt",
        name=html.escape(product_name(product, language)),
        stock=html.escape(str(product_stock_count(product))),
        price=html.escape(product["price"]),
    )


def deposit_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(tr(language, "binance_btn"), callback_data="binance_pay")],
        [
            InlineKeyboardButton(tr(language, "help_btn"), callback_data="deposit_help"),
            InlineKeyboardButton(tr(language, "main_menu_btn"), callback_data="menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_back_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(tr(language, "back_deposit_btn"), callback_data="topup")],
        [InlineKeyboardButton(tr(language, "main_menu_btn"), callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_text(language: str) -> str:
    return tr(
        language,
        "settings",
        language=language_label(language),
        currency=CURRENCY,
    )


def settings_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                tr(language, "change_language_btn"), callback_data="change_language"
            )
        ],
        [
            InlineKeyboardButton(
                tr(language, "change_currency_btn"), callback_data="change_currency"
            )
        ],
        [InlineKeyboardButton(tr(language, "home_btn"), callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def language_menu(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("\U0001f1ec\U0001f1e7 English", callback_data="set_lang_en")],
        [InlineKeyboardButton("\U0001f1eb\U0001f1f7 French", callback_data="set_lang_fr")],
        [InlineKeyboardButton(tr(language, "home_btn"), callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    language = get_language(context)
    bot_name = await get_bot_name(context)
    balance = get_user_balance(user.id)
    await message.reply_text(
        welcome_text(language, bot_name, balance), reply_markup=main_menu(language)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    await message.reply_text(tr(get_language(context), "help"))


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    clear_invoice_state(context)
    language = get_language(context)
    await message.reply_text(tr(language, "shop"), reply_markup=shop_menu(language))


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    await message.reply_text(f"Your Telegram ID: {user.id}")


async def ask_purchase_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    product_id: str,
    payment_method: str,
) -> None:
    query = update.callback_query
    if query is None:
        return

    language = get_language(context)
    product = find_product(product_id)
    if product is None:
        await query.edit_message_text(
            tr(language, "product_not_found"), reply_markup=shop_menu(language)
        )
        return

    if product_stock_count(product) <= 0:
        await query.edit_message_text(
            tr(language, "product_unavailable"),
            reply_markup=out_of_stock_menu(language),
        )
        return

    clear_invoice_state(context)
    context.user_data["awaiting_purchase_quantity"] = True
    context.user_data["purchase_payment_method"] = payment_method
    context.user_data["product_id"] = product_id
    await query.edit_message_text(
        quantity_prompt_text(product, language),
        reply_markup=product_payment_back_menu(language, product_id),
        parse_mode="HTML",
    )


async def complete_balance_purchase(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    language: str,
    product_id: str,
    quantity: int,
) -> None:
    data = load_db()
    product = find_product_in_data(data, product_id)
    if product is None:
        clear_invoice_state(context)
        await message.reply_text(
            tr(language, "product_not_found"), reply_markup=shop_menu(language)
        )
        return

    stock = product_stock_count(product)
    if stock < quantity:
        await message.reply_text(
            tr(language, "not_enough_stock", stock=str(stock)),
            reply_markup=out_of_stock_menu(language) if stock == 0 else product_payment_back_menu(language, product_id),
            parse_mode="HTML",
        )
        return

    total_price = product_total_price(product, quantity)
    total_price_text = format_deposit_amount(total_price)
    user_record = ensure_user(data, user.id)
    balance = user_record["balance"]
    if Decimal(balance) < total_price:
        clear_invoice_state(context)
        await message.reply_text(
            tr(
                language,
                "insufficient_balance",
                price=html.escape(total_price_text),
                balance=html.escape(balance),
            ),
            reply_markup=product_menu(language, product_id),
            parse_mode="HTML",
        )
        return

    product, coupons = consume_product_delivery(data, product_id, quantity)
    if product is None or coupons is None:
        clear_invoice_state(context)
        await message.reply_text(
            tr(language, "product_unavailable"),
            reply_markup=out_of_stock_menu(language),
        )
        return

    new_balance = subtract_user_balance(data, user.id, total_price)
    if new_balance is None:
        clear_invoice_state(context)
        await message.reply_text(
            tr(
                language,
                "insufficient_balance",
                price=html.escape(total_price_text),
                balance=html.escape(balance),
            ),
            reply_markup=product_menu(language, product_id),
            parse_mode="HTML",
        )
        return

    delivery = format_delivery(coupons)
    order_id = create_order_id()
    data.setdefault("orders", {})[order_id] = {
        "order_id": order_id,
        "user_id": user.id,
        "product_id": product_id,
        "product_name": product_name(product, language),
        "quantity": quantity,
        "unit_price": product["price"],
        "price": total_price_text,
        "delivery": delivery,
        "payment_method": "balance",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_db(data)
    clear_invoice_state(context)

    await message.reply_text(
        tr(
            language,
            "purchase_success",
            order_id=html.escape(order_id),
            name=html.escape(product_name(product, language)),
            quantity=html.escape(str(quantity)),
            price=html.escape(total_price_text),
            balance=html.escape(new_balance),
            delivery=html.escape(delivery),
        ),
        reply_markup=main_menu(language),
        parse_mode="HTML",
    )


async def create_product_binance_invoice(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    language: str,
    product_id: str,
    quantity: int,
) -> None:
    product = find_product(product_id)
    if product is None:
        clear_invoice_state(context)
        await message.reply_text(
            tr(language, "product_not_found"), reply_markup=shop_menu(language)
        )
        return

    stock = product_stock_count(product)
    if stock < quantity:
        await message.reply_text(
            tr(language, "not_enough_stock", stock=str(stock)),
            reply_markup=out_of_stock_menu(language) if stock == 0 else product_payment_back_menu(language, product_id),
            parse_mode="HTML",
        )
        return

    pay_id = get_binance_pay_id()
    if not pay_id or pay_id == BINANCE_PAY_ID_PLACEHOLDER:
        clear_invoice_state(context)
        await message.reply_text(
            tr(language, "binance_id_missing"),
            reply_markup=product_menu(language, product_id),
        )
        return

    total_price_text = format_deposit_amount(product_total_price(product, quantity))
    invoice_id = create_invoice_id()
    context.user_data["awaiting_purchase_quantity"] = False
    context.user_data["awaiting_transaction_id"] = True
    context.user_data["deposit_amount"] = total_price_text
    context.user_data["payment_purpose"] = "purchase"
    context.user_data["product_id"] = product_id
    context.user_data["product_name"] = product_name(product, language)
    context.user_data["product_quantity"] = quantity
    context.user_data["unit_price"] = product["price"]
    context.user_data["invoice_id"] = invoice_id
    context.user_data["invoice_expires_at"] = datetime.now(timezone.utc) + timedelta(
        minutes=INVOICE_EXPIRE_MINUTES
    )

    await message.reply_text(
        binance_invoice_text(language, invoice_id, pay_id, total_price_text),
        reply_markup=product_payment_back_menu(language, product_id),
        parse_mode="HTML",
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    if not is_admin(user.id):
        await message.reply_text("Admin only.")
        return

    clear_admin_state(context)
    await message.reply_text(
        "\U0001f527 Admin panel\n\nChoose what you want to manage.",
        reply_markup=admin_menu(),
    )


async def handle_admin_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    message = update.effective_message
    user = update.effective_user
    flow = context.user_data.get("admin_flow")
    if message is None or message.text is None or user is None or flow is None:
        return False

    if not is_admin(user.id):
        return False

    text = message.text.strip()
    draft = context.user_data.setdefault("admin_product_draft", {})

    if flow == "add_product_name_en":
        draft["name_en"] = text
        context.user_data["admin_flow"] = "add_product_name_fr"
        await message.reply_text("Send product French name, or `-` to copy English.")
        return True

    if flow == "add_product_name_fr":
        draft["name_fr"] = draft["name_en"] if text == "-" else text
        context.user_data["admin_flow"] = "add_product_price"
        await message.reply_text("Send product price, example: `0.01`.")
        return True

    if flow == "add_product_price":
        price = parse_deposit_amount(text)
        if price is None or price <= Decimal("0"):
            await message.reply_text("Invalid price. Send a number like `0.01`.")
            return True

        draft["price"] = format_deposit_amount(price)
        context.user_data["admin_flow"] = "add_product_desc_en"
        await message.reply_text("Send English description.")
        return True

    if flow == "add_product_desc_en":
        draft["description_en"] = text
        context.user_data["admin_flow"] = "add_product_desc_fr"
        await message.reply_text("Send French description, or `-` to copy English.")
        return True

    if flow == "add_product_desc_fr":
        draft["description_fr"] = draft["description_en"] if text == "-" else text
        context.user_data["admin_flow"] = "add_product_coupons"
        await message.reply_text(
            "Send coupon codes, one per line or separated by commas.\n"
            "Send `-`, `0`, or `skip` to create the product with 0 stock."
        )
        return True

    if flow == "add_product_coupons":
        coupons = (
            []
            if text.lower() in {"-", "0", "skip", "none"}
            else parse_coupon_list(text)
        )
        product = {
            "id": make_product_id(),
            "icon": "\U0001f3ab",
            "price": draft["price"],
            "type": "coupon",
            "name": {
                "en": draft["name_en"],
                "fr": draft["name_fr"],
            },
            "description": {
                "en": draft["description_en"],
                "fr": draft["description_fr"],
            },
            "coupons": coupons,
        }

        products = get_products()
        products.append(product)
        save_products(products)
        clear_admin_state(context)
        await message.reply_text(
            "\u2705 Product added.\n\n"
            f"ID: `{product['id']}`\n"
            f"Name: {product['name']['en']}\n"
            f"Price: ${product['price']}\n"
            f"Stock: {len(coupons)}",
            reply_markup=admin_menu(),
        )
        return True

    if flow == "add_stock":
        product_id = context.user_data.get("admin_stock_product_id")
        coupons = TEST_COUPONS.copy() if text == "-" else parse_coupon_list(text)
        if not product_id:
            clear_admin_state(context)
            await message.reply_text("Stock edit state expired.", reply_markup=admin_menu())
            return True

        if not coupons:
            await message.reply_text("Send at least one coupon, or `-` for test coupons.")
            return True

        products = get_products()
        product = next(
            (item for item in products if item.get("id") == product_id),
            None,
        )
        if product is None:
            clear_admin_state(context)
            await message.reply_text("Product not found.", reply_markup=admin_products_menu())
            return True

        product.setdefault("coupons", []).extend(coupons)
        save_products(products)
        stock = product_stock_count(product)
        clear_admin_state(context)
        await message.reply_text(
            f"\u2705 Added {len(coupons)} coupons.\n"
            f"New stock: {stock}",
            reply_markup=admin_product_menu(product_id),
        )
        return True

    if flow == "add_support_contact":
        contact = text.strip()
        if not contact:
            await message.reply_text("Send a valid contact, example: @username")
            return True

        contacts = get_support_contacts()
        contacts.append(contact)
        save_support_contacts(contacts)
        clear_admin_state(context)
        await message.reply_text(
            "\u2705 Support contact added.",
            reply_markup=admin_support_contacts_menu(),
        )
        return True

    if flow == "edit_text":
        lang = context.user_data.get("admin_text_lang")
        key = context.user_data.get("admin_text_key")
        if lang not in TEXT or key not in TEXT[lang]:
            clear_admin_state(context)
            await message.reply_text("Text edit state expired.", reply_markup=admin_menu())
            return True

        data = load_db()
        data.setdefault("text_overrides", {}).setdefault(lang, {})[key] = message.text
        save_db(data)
        clear_admin_state(context)
        await message.reply_text(
            f"\u2705 Text updated: `{lang}.{key}`", reply_markup=admin_menu()
        )
        return True

    return False


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or message.text is None:
        return

    if await handle_admin_text(update, context):
        return

    language = get_language(context)
    if context.user_data.get("awaiting_purchase_quantity"):
        user = update.effective_user
        if user is None:
            return

        quantity = parse_quantity(message.text)
        if quantity is None:
            await message.reply_text(
                tr(language, "invalid_quantity"),
                reply_markup=product_payment_back_menu(
                    language, str(context.user_data.get("product_id") or "")
                ),
            )
            return

        product_id = str(context.user_data.get("product_id") or "")
        payment_method = str(context.user_data.get("purchase_payment_method") or "balance")
        product = find_product(product_id)
        if product is None:
            clear_invoice_state(context)
            await message.reply_text(
                tr(language, "product_not_found"), reply_markup=shop_menu(language)
            )
            return

        stock = product_stock_count(product)
        if quantity > stock:
            await message.reply_text(
                tr(language, "not_enough_stock", stock=str(stock)),
                reply_markup=out_of_stock_menu(language)
                if stock == 0
                else product_payment_back_menu(language, product_id),
                parse_mode="HTML",
            )
            return

        if payment_method == "binance":
            await create_product_binance_invoice(
                message, context, language, product_id, quantity
            )
            return

        await complete_balance_purchase(
            message, context, user, language, product_id, quantity
        )
        return

    if context.user_data.get("awaiting_deposit_amount"):
        amount = parse_deposit_amount(message.text)
        if amount is None:
            await message.reply_text(
                tr(language, "invalid_deposit_amount"),
                reply_markup=deposit_back_menu(language),
            )
            return

        if amount < MIN_DEPOSIT_USDT:
            await message.reply_text(
                tr(language, "amount_too_low"),
                reply_markup=deposit_back_menu(language),
            )
            return

        pay_id = get_binance_pay_id()
        if not pay_id or pay_id == BINANCE_PAY_ID_PLACEHOLDER:
            clear_invoice_state(context)
            await message.reply_text(
                tr(language, "binance_id_missing"),
                reply_markup=deposit_back_menu(language),
            )
            return

        amount_text = format_deposit_amount(amount)
        invoice_id = create_invoice_id()
        context.user_data["awaiting_deposit_amount"] = False
        context.user_data["awaiting_transaction_id"] = True
        context.user_data["deposit_amount"] = amount_text
        context.user_data["payment_purpose"] = "topup"
        context.user_data["invoice_id"] = invoice_id
        context.user_data["invoice_expires_at"] = datetime.now(timezone.utc) + timedelta(
            minutes=INVOICE_EXPIRE_MINUTES
        )

        await message.reply_text(
            binance_invoice_text(language, invoice_id, pay_id, amount_text),
            reply_markup=deposit_back_menu(language),
            parse_mode="HTML",
        )
        return

    if not context.user_data.get("awaiting_transaction_id"):
        await message.reply_text(tr(language, "help"))
        return

    expires_at = context.user_data.get("invoice_expires_at")
    if isinstance(expires_at, datetime) and datetime.now(timezone.utc) > expires_at:
        expired_purpose = context.user_data.get("payment_purpose")
        expired_product_id = str(context.user_data.get("product_id") or "")
        expired_reply_markup = (
            product_menu(language, expired_product_id)
            if expired_purpose == "purchase" and find_product(expired_product_id)
            else deposit_menu(language)
        )
        clear_invoice_state(context)
        await message.reply_text(
            tr(language, "invoice_expired"), reply_markup=expired_reply_markup
        )
        return

    transaction_id = message.text.strip()
    if not transaction_id:
        return

    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return

    invoice_id = str(context.user_data.get("invoice_id") or create_invoice_id())
    amount_text = str(context.user_data.get("deposit_amount") or "0")
    payment_purpose = str(context.user_data.get("payment_purpose") or "topup")
    product_id = context.user_data.get("product_id")
    pending_product_name = context.user_data.get("product_name")
    product_quantity = int(context.user_data.get("product_quantity") or 1)
    unit_price = str(context.user_data.get("unit_price") or "")
    deposit = {
        "invoice_id": invoice_id,
        "user_id": user.id,
        "chat_id": chat.id,
        "full_name": user.full_name,
        "username": user.username,
        "amount": amount_text,
        "transaction_id": transaction_id,
        "language": language,
        "purpose": payment_purpose,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if payment_purpose == "purchase":
        deposit["product_id"] = str(product_id or "")
        deposit["product_name"] = str(pending_product_name or product_id or "-")
        deposit["quantity"] = product_quantity
        deposit["unit_price"] = unit_price

    context.user_data["last_transaction_id"] = transaction_id
    save_pending_deposit(deposit)
    admin_notified = await notify_admin_deposit(context, deposit)
    clear_invoice_state(context)

    if payment_purpose == "purchase":
        response_key = "payment_received" if admin_notified else "payment_admin_not_configured"
    else:
        response_key = "transaction_received" if admin_notified else "admin_not_configured"
    await message.reply_text(
        tr(
            language,
            response_key,
            transaction_id=html.escape(transaction_id),
        ),
        reply_markup=main_menu(language),
        parse_mode="HTML",
    )


async def handle_admin_decision(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    invoice_id: str,
) -> None:
    query = update.callback_query
    admin_user = update.effective_user
    if query is None or admin_user is None:
        return

    admin_id = get_admin_id()
    if admin_id is None or admin_user.id != admin_id:
        await query.answer("Admin only.", show_alert=True)
        return

    data = load_db()
    deposits = data.setdefault("pending_deposits", {})
    deposit = deposits.get(invoice_id)
    if deposit is None:
        await query.answer("Deposit not found.", show_alert=True)
        return

    if deposit.get("status") != "pending":
        await query.answer("Deposit already processed.", show_alert=True)
        return

    language = deposit.get("language", DEFAULT_LANGUAGE)
    if language not in TEXT:
        language = DEFAULT_LANGUAGE

    if action == "confirm":
        if deposit.get("purpose") == "purchase":
            product_id = str(deposit.get("product_id") or "")
            quantity = int(deposit.get("quantity") or 1)
            product, coupons = consume_product_delivery(data, product_id, quantity)
            if product is None:
                await query.answer("Product not found.", show_alert=True)
                return

            if coupons is None:
                await query.answer("Product unavailable.", show_alert=True)
                return

            delivery = format_delivery(coupons)
            order_id = create_order_id()
            data.setdefault("orders", {})[order_id] = {
                "order_id": order_id,
                "user_id": deposit["user_id"],
                "product_id": product_id,
                "product_name": product_name(product, language),
                "quantity": quantity,
                "unit_price": deposit.get("unit_price") or product["price"],
                "price": deposit["amount"],
                "delivery": delivery,
                "payment_method": "binance",
                "invoice_id": deposit["invoice_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            deposit["status"] = "confirmed"
            deposit["confirmed_at"] = datetime.now(timezone.utc).isoformat()
            save_db(data)

            await context.bot.send_message(
                chat_id=deposit["chat_id"],
                text=tr(
                    language,
                    "purchase_success_binance",
                    order_id=html.escape(order_id),
                    name=html.escape(product_name(product, language)),
                    quantity=html.escape(str(quantity)),
                    price=html.escape(deposit["amount"]),
                    delivery=html.escape(delivery),
                ),
                reply_markup=main_menu(language),
                parse_mode="HTML",
            )
            await query.edit_message_text(
                admin_deposit_text(deposit) + "\n\n\u2705 <b>Confirmed</b>",
                parse_mode="HTML",
            )
            await query.answer("Product payment confirmed.")
            return

        amount = Decimal(deposit["amount"])
        new_balance = add_user_balance(data, deposit["user_id"], amount)
        deposit["status"] = "confirmed"
        deposit["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        save_db(data)

        await context.bot.send_message(
            chat_id=deposit["chat_id"],
            text=tr(
                language,
                "deposit_confirmed",
                amount=html.escape(deposit["amount"]),
                balance=html.escape(new_balance),
            ),
            reply_markup=main_menu(language),
            parse_mode="HTML",
        )
        await query.edit_message_text(
            admin_deposit_text(deposit) + "\n\n\u2705 <b>Confirmed</b>",
            parse_mode="HTML",
        )
        await query.answer("Deposit confirmed.")
        return

    deposit["status"] = "rejected"
    deposit["rejected_at"] = datetime.now(timezone.utc).isoformat()
    save_db(data)

    await context.bot.send_message(
        chat_id=deposit["chat_id"],
        text=tr(
            language,
            "payment_rejected" if deposit.get("purpose") == "purchase" else "deposit_rejected",
            invoice_id=html.escape(deposit["invoice_id"]),
        ),
        reply_markup=main_menu(language),
        parse_mode="HTML",
    )
    await query.edit_message_text(
        admin_deposit_text(deposit) + "\n\n\u274c <b>Rejected</b>",
        parse_mode="HTML",
    )
    await query.answer("Deposit rejected.")


async def handle_purchase(
    update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str
) -> None:
    await ask_purchase_quantity(update, context, product_id, "balance")


async def handle_product_binance_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str
) -> None:
    await ask_purchase_quantity(update, context, product_id, "binance")


async def handle_admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> bool:
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None or not data.startswith("admin_"):
        return False

    if not is_admin(user.id):
        await query.answer("Admin only.", show_alert=True)
        return True

    await query.answer()

    if data in {"admin_panel", "admin_cancel"}:
        clear_admin_state(context)
        await query.edit_message_text(
            "\U0001f527 Admin panel\n\nChoose what you want to manage.",
            reply_markup=admin_menu(),
        )
        return True

    if data == "admin_add_product":
        clear_admin_state(context)
        context.user_data["admin_flow"] = "add_product_name_en"
        context.user_data["admin_product_draft"] = {}
        await query.edit_message_text(
            "\u2795 Add product\n\nSend product English name."
        )
        return True

    if data == "admin_products":
        await query.edit_message_text(
            "\U0001f4e6 Products\n\nChoose a product to manage stock.",
            reply_markup=admin_products_menu(),
        )
        return True

    if data == "admin_support_contacts":
        await query.edit_message_text(
            admin_support_contacts_text(),
            reply_markup=admin_support_contacts_menu(),
        )
        return True

    if data == "admin_add_support_contact":
        clear_admin_state(context)
        context.user_data["admin_flow"] = "add_support_contact"
        await query.edit_message_text(
            "Send the support contact to add.\n\n"
            "Examples:\n"
            "@ACH020\n"
            "https://t.me/ACH020\n"
            "Support: @ACH020"
        )
        return True

    if data.startswith("admin_delete_support:"):
        raw_index = data.removeprefix("admin_delete_support:")
        try:
            index = int(raw_index)
        except ValueError:
            await query.edit_message_text(
                "Contact not found.", reply_markup=admin_support_contacts_menu()
            )
            return True

        contacts = get_support_contacts()
        if index < 0 or index >= len(contacts):
            await query.edit_message_text(
                "Contact not found.", reply_markup=admin_support_contacts_menu()
            )
            return True

        contacts.pop(index)
        save_support_contacts(contacts)
        await query.edit_message_text(
            "\u2705 Support contact deleted.",
            reply_markup=admin_support_contacts_menu(),
        )
        return True

    if data.startswith("admin_product:"):
        product_id = data.removeprefix("admin_product:")
        product = find_product(product_id)
        if product is None:
            await query.edit_message_text(
                "Product not found.", reply_markup=admin_products_menu()
            )
            return True

        await query.edit_message_text(
            admin_product_text(product),
            reply_markup=admin_product_menu(product_id),
            parse_mode="HTML",
        )
        return True

    if data.startswith("admin_add_stock:"):
        product_id = data.removeprefix("admin_add_stock:")
        product = find_product(product_id)
        if product is None:
            await query.edit_message_text(
                "Product not found.", reply_markup=admin_products_menu()
            )
            return True

        context.user_data["admin_flow"] = "add_stock"
        context.user_data["admin_stock_product_id"] = product_id
        await query.edit_message_text(
            "Send coupons to add to this product, one per line or separated by commas.\n"
            "Send `-` to add default test coupons."
        )
        return True

    if data.startswith("admin_delete_product:"):
        product_id = data.removeprefix("admin_delete_product:")
        products = get_products()
        next_products = [product for product in products if product["id"] != product_id]
        if len(next_products) == len(products):
            await query.edit_message_text(
                "Product not found.", reply_markup=admin_products_menu()
            )
            return True

        save_products(next_products)
        await query.edit_message_text(
            "\u2705 Product deleted.", reply_markup=admin_products_menu()
        )
        return True

    if data == "admin_reset_products":
        save_products(default_products())
        await query.edit_message_text(
            "\u2705 Products reset to defaults.", reply_markup=admin_menu()
        )
        return True

    if data == "admin_reset_text":
        db = load_db()
        db["text_overrides"] = {}
        save_db(db)
        await query.edit_message_text(
            "\u2705 Text overrides reset.", reply_markup=admin_menu()
        )
        return True

    if data == "admin_edit_text":
        clear_admin_state(context)
        await query.edit_message_text(
            "\u270f Edit text\n\nChoose language.",
            reply_markup=admin_text_language_menu(),
        )
        return True

    if data.startswith("admin_edit_direct:"):
        key = data.removeprefix("admin_edit_direct:")
        if key != "channel":
            await query.edit_message_text("Text key not found.", reply_markup=admin_menu())
            return True

        clear_admin_state(context)
        await query.edit_message_text(
            f"\u270f Edit {admin_text_label(key)}\n\nChoose language.",
            reply_markup=admin_direct_text_language_menu(key),
        )
        return True

    if data.startswith("admin_direct_text_lang:"):
        _, key, lang = data.split(":", 2)
        if key != "channel" or lang not in TEXT:
            await query.edit_message_text("Text key not found.", reply_markup=admin_menu())
            return True

        db = load_db()
        current_value = (
            db.get("text_overrides", {}).get(lang, {}).get(key)
            or TEXT[lang][key]
        )
        context.user_data["admin_flow"] = "edit_text"
        context.user_data["admin_text_lang"] = lang
        context.user_data["admin_text_key"] = key
        await query.edit_message_text(
            f"\u270f Editing <b>{html.escape(admin_text_label(key))}</b> "
            f"(<code>{html.escape(lang)}</code>)\n\n"
            "Send the new text as your next message.\n\n"
            f"<b>Current:</b>\n<code>{html.escape(current_value)}</code>",
            parse_mode="HTML",
        )
        return True

    if data.startswith("admin_text_lang:"):
        lang = data.removeprefix("admin_text_lang:")
        if lang not in TEXT:
            await query.edit_message_text(
                "Language not found.", reply_markup=admin_text_language_menu()
            )
            return True

        await query.edit_message_text(
            f"\u270f Edit text `{lang}`\n\nChoose text key.",
            reply_markup=admin_text_key_menu(lang),
        )
        return True

    if data.startswith("admin_text_key:"):
        _, lang, key = data.split(":", 2)
        if lang not in TEXT or key not in TEXT[lang]:
            await query.edit_message_text(
                "Text key not found.", reply_markup=admin_text_language_menu()
            )
            return True

        db = load_db()
        current_value = (
            db.get("text_overrides", {}).get(lang, {}).get(key)
            or TEXT[lang][key]
        )
        context.user_data["admin_flow"] = "edit_text"
        context.user_data["admin_text_lang"] = lang
        context.user_data["admin_text_key"] = key
        await query.edit_message_text(
            f"\u270f Editing <b>{html.escape(lang)}.{html.escape(key)}</b>\n\n"
            "Send the new text as your next message.\n"
            "Keep placeholders like <code>{balance}</code>, <code>{bot_name}</code>, "
            "or <code>{order_id}</code> if this text uses them.\n\n"
            f"<b>Current:</b>\n<code>{html.escape(current_value)}</code>",
            parse_mode="HTML",
        )
        return True

    return False


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    data = query.data or ""
    language = get_language(context)

    if data.startswith("admin_confirm:"):
        await handle_admin_decision(
            update, context, "confirm", data.removeprefix("admin_confirm:")
        )
        return

    if data.startswith("admin_reject:"):
        await handle_admin_decision(
            update, context, "reject", data.removeprefix("admin_reject:")
        )
        return

    if await handle_admin_callback(update, context, data):
        return

    if data != "binance_pay":
        clear_invoice_state(context)

    if data == "change_currency":
        await query.answer(tr(language, "currency_soon"), show_alert=True)
        return

    if data.startswith("set_lang_"):
        new_language = data.removeprefix("set_lang_")
        set_language(context, new_language)
        language = get_language(context)
        await query.answer(tr(language, "language_changed"))
        await query.edit_message_text(
            settings_text(language), reply_markup=settings_menu(language)
        )
        return

    await query.answer()

    if data == "menu":
        user = update.effective_user
        if user is None:
            return

        bot_name = await get_bot_name(context)
        balance = get_user_balance(user.id)
        await query.edit_message_text(
            welcome_text(language, bot_name, balance), reply_markup=main_menu(language)
        )
        return

    if data == "shop":
        await query.edit_message_text(tr(language, "shop"), reply_markup=shop_menu(language))
        return

    if data.startswith("product:"):
        user = update.effective_user
        if user is None:
            return

        product_id = data.removeprefix("product:")
        product = find_product(product_id)
        if product is None:
            await query.edit_message_text(
                tr(language, "product_not_found"), reply_markup=shop_menu(language)
            )
            return

        balance = get_user_balance(user.id)
        reply_markup = (
            product_menu(language, product_id)
            if product_stock_count(product) > 0
            else out_of_stock_menu(language)
        )
        await query.edit_message_text(
            product_text(product, language, balance),
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return

    if data.startswith("buy:"):
        await handle_purchase(update, context, data.removeprefix("buy:"))
        return

    if data.startswith("pay_product_binance:"):
        await handle_product_binance_payment(
            update, context, data.removeprefix("pay_product_binance:")
        )
        return

    if data == "topup":
        await query.edit_message_text(
            tr(language, "deposit"), reply_markup=deposit_menu(language)
        )
        return

    if data == "binance_pay":
        clear_invoice_state(context)
        pay_id = get_binance_pay_id()
        if not pay_id or pay_id == BINANCE_PAY_ID_PLACEHOLDER:
            await query.edit_message_text(
                tr(language, "binance_id_missing"),
                reply_markup=deposit_back_menu(language),
            )
            return

        context.user_data["awaiting_deposit_amount"] = True
        await query.edit_message_text(
            tr(language, "enter_deposit_amount"),
            reply_markup=deposit_back_menu(language),
        )
        return

    if data == "deposit_help":
        await query.edit_message_text(
            tr(language, "deposit_help"), reply_markup=deposit_back_menu(language)
        )
        return

    if data == "settings":
        await query.edit_message_text(
            settings_text(language), reply_markup=settings_menu(language)
        )
        return

    if data in {"language", "change_language"}:
        await query.edit_message_text(
            tr(language, "language"), reply_markup=language_menu(language)
        )
        return

    if data == "history":
        user = update.effective_user
        if user is None:
            return

        await query.edit_message_text(
            history_text(user.id, language),
            reply_markup=back_menu(language),
            parse_mode="HTML",
        )
        return

    if data == "support":
        await query.edit_message_text(support_text(language), reply_markup=back_menu(language))
        return

    if data == "channel":
        await query.edit_message_text(tr(language, data), reply_markup=back_menu(language))
        return

    await query.edit_message_text(
        tr(language, "not_ready"), reply_markup=back_menu(language)
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if isinstance(error, BadRequest) and "Message is not modified" in str(error):
        return

    print(f"Bot error: {error}")


async def setup_bot_commands(application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Open the main menu"),
            BotCommand("product", "Browse products"),
        ]
    )


def main() -> None:
    token = get_token()

    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_pool_timeout(30)
        .post_init(setup_bot_commands)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("product", products_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(bootstrap_retries=-1)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    except InvalidToken as exc:
        raise SystemExit(
            "BOT_TOKEN was rejected by Telegram. Check the token from @BotFather."
        ) from exc
