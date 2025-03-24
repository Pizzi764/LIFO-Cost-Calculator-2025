import csv
import requests
import datetime
from io import StringIO
import logging
import os

# File di cache
EXCHANGE_RATES_CACHE = "exchange_rates.txt"
HISTORICAL_PRICES_CACHE = "historical_prices.txt"

def load_cached_exchange_rates():
    """Carica i tassi EUR/USD dal file di cache."""
    rates = {}
    if os.path.exists(EXCHANGE_RATES_CACHE):
        with open(EXCHANGE_RATES_CACHE, 'r') as f:
            for line in f:
                if line.strip():
                    date_str, rate = line.strip().split(',')
                    rates[date_str] = float(rate)
    return rates

def save_exchange_rate_to_cache(date_str, rate):
    """Salva un tasso EUR/USD nel file di cache."""
    with open(EXCHANGE_RATES_CACHE, 'a') as f:
        f.write(f"{date_str},{rate}\n")

def load_cached_historical_prices():
    """Carica i prezzi storici dal file di cache."""
    prices = {}
    if os.path.exists(HISTORICAL_PRICES_CACHE):
        with open(HISTORICAL_PRICES_CACHE, 'r') as f:
            for line in f:
                if line.strip():
                    date_str, symbol, price = line.strip().split(',')
                    if date_str not in prices:
                        prices[date_str] = {}
                    prices[date_str][symbol] = float(price)
    return prices

def save_historical_price_to_cache(date_str, symbol, price):
    """Salva un prezzo storico nel file di cache."""
    with open(HISTORICAL_PRICES_CACHE, 'a') as f:
        f.write(f"{date_str},{symbol},{price}\n")

def get_EURUSD_exchange_rate(data, attempts=5):
    """
    Ottiene il tasso di cambio EUR/USD per una data specifica (1 EUR = X USD).
    Prima controlla la cache, poi fa una richiesta web e salva il risultato.

    Args:
        data (datetime.datetime): La data per la quale ottenere il tasso.
        attempts (int): Numero massimo di giorni precedenti da provare.

    Returns:
        float or None: Il tasso di cambio EUR/USD o None se non disponibile.
    """
    if not isinstance(data, datetime.datetime):
        raise ValueError("Il parametro 'data' deve essere un oggetto datetime")

    ref_date = data.strftime("%Y-%m-%d")
    
    # Controlla la cache
    cached_rates = load_cached_exchange_rates()
    if ref_date in cached_rates:
        logging.debug(f"Tasso EUR/USD trovato in cache per {ref_date}: {cached_rates[ref_date]}")
        return cached_rates[ref_date]

    # Richiesta web
    url = f"https://tassidicambio.bancaditalia.it/terzevalute-wf-web/rest/v1.0/dailyRates?referenceDate={ref_date}&baseCurrencyIsoCode=USD&currencyIsoCode=EUR"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        logging.debug(f"Risposta grezza per {ref_date}: {response.text}")
        
        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            eur_usd_rate = float(row["Quotazione"])  # 1 EUR = X USD
            logging.debug(f"Tasso di cambio EUR/USD per {ref_date}: {eur_usd_rate:.6f}")
            save_exchange_rate_to_cache(ref_date, eur_usd_rate)  # Salva nella cache
            return eur_usd_rate

    except requests.exceptions.RequestException as e:
        logging.error(f"Errore nella richiesta del tasso di cambio EUR/USD per {ref_date}: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Errore nel parsing del CSV per {ref_date}: {e}")

    # Fallback al giorno precedente
    if attempts > 0:
        previous_day = data - datetime.timedelta(days=1)
        logging.debug(f"Tasso non trovato per {ref_date}, provo il giorno precedente: {previous_day.strftime('%Y-%m-%d')}")
        return get_EURUSD_exchange_rate(previous_day, attempts - 1)
    else:
        logging.error(f"Impossibile ottenere il tasso EUR/USD dopo {attempts} tentativi")
        return None

def get_historical_price_EUR(symbol, date):
    """
    Ottiene il prezzo storico di una criptovaluta in EUR per una data specifica.
    Usa dati hardcoded e cache.

    Args:
        symbol (str): Simbolo della criptovaluta (es. 'BTC', 'ETH').
        date (datetime.datetime): Data per la quale ottenere il prezzo.

    Returns:
        float: Il prezzo in EUR o 0 se non trovato.
    """
    if not isinstance(date, datetime.datetime):
        raise ValueError("Il parametro 'date' deve essere un oggetto datetime")

    if symbol == "EUR":
        return 1

    if symbol == "USD":
        rate = get_EURUSD_exchange_rate(date)
        return 1 / rate if rate else None

    target_date = date.strftime("%Y-%m-%d")

    # Dati hardcoded
    historical_data = [
        {"date": "2023-12-31", "value": 38230, "symbol": "BTC"},
        {"date": "2024-12-31", "value": 89686.59, "symbol": "BTC"},
        {"date": "2023-12-31", "value": 2063.65, "symbol": "ETH"},
        {"date": "2024-12-31", "value": 3202.60, "symbol": "ETH"},
        {"date": "2023-12-31", "value": 0.08949, "symbol": "CRO"},
        {"date": "2024-12-31", "value": 0.1355, "symbol": "CRO"},
        {"date": "2023-12-31", "value": 0.5562, "symbol": "XRP"},
        {"date": "2023-12-31", "value": 0.9043, "symbol": "USDT"},
        {"date": "2023-12-31", "value": 0.9046, "symbol": "USDC"},
        {"date": "2023-12-31", "value": 1.4067, "symbol": "ARB"},
        {"date": "2024-12-31", "value": 296.61, "symbol": "AAVE"},
        {"date": "2024-12-31", "value": 1.84, "symbol": "SNX"},
        {"date": "2024-12-31", "value": 12.70, "symbol": "UNI"},
        {"date": "2024-12-31", "value": 4.3035, "symbol": "RUNE"},
        {"date": "2024-12-31", "value": 26.05, "symbol": "GMX"},
        {"date": "2023-12-09", "value": 40586.46, "symbol": "BTC"}
    ]

    # Controlla la cache
    cached_prices = load_cached_historical_prices()
    if target_date in cached_prices and symbol in cached_prices[target_date]:
        logging.debug(f"Prezzo storico trovato in cache per {symbol} il {target_date}: {cached_prices[target_date][symbol]}")
        return cached_prices[target_date][symbol]

    # Cerca nei dati hardcoded
    for data_point in historical_data:
        if data_point["date"] == target_date and data_point["symbol"] == symbol:
            logging.debug(f"Prezzo storico trovato nei dati hardcoded per {symbol} il {target_date}: {data_point['value']}")
            save_historical_price_to_cache(target_date, symbol, data_point["value"])  # Salva nella cache
            return data_point["value"]

    # Se non trovato, restituisci 0 (come nell'originale)
    logging.warning(f"Nessun dato storico trovato per {symbol} il {target_date}, restituisco 0")
    return 0