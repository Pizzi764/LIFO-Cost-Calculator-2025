import csv
import requests
import datetime
from io import StringIO

def get_historical_price_EUR(symbol, date):

    if not isinstance(date, datetime.datetime):
        raise ValueError("Il parametro 'date' deve essere un oggetto datetime")

    if symbol == "EUR":
        return 1

    if symbol == "USD":
        return 1/get_EURUSD_exchange_rate(date)

    # Array di dati storici (data, valore, simbolo)
    historical_data = [
        # Valori al 31-12-2023
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


        # Altri valori che servono per TX Fiscalmente rilevanti
        {"date": "2023-12-09", "value": 40586.46, "symbol": "BTC"}

    ]

    # Confronta solo il giorno del timestamp con la data fornita
    target_date = date.strftime("%Y-%m-%d")

    # Cerca il valore corrispondente alla data e al simbolo forniti
    for data_point in historical_data:
        if data_point["date"] == target_date and data_point["symbol"] == symbol:
            return data_point["value"]

    # Solleva un'eccezione se non trova corrispondenze
    #raise ValueError(f"Nessun dato storico trovato per il simbolo {symbol} e la data {target_date}")
    return 0


    """
    while True:
        try:
            price = float(input(f"Inserisci il valore storico per {symbol} alla data {date} in euro: "))
            return price
except ValueError:
            print("Per favore, inserisci un valore numerico valido.")
    

    
    Ottiene il prezzo storico di una criptovaluta per una data specifica in Euro.

    Args:
        symbol (str): Il simbolo della criptovaluta (es. 'BTC', 'ETH', 'XRP').
        date (str): La data nel formato 'YYYY-MM-DD'.

    Returns:
        float: Il prezzo storico della criptovaluta in Euro per la data specificata.
    """
    '''
    api_key = '6befb01c-8187-417c-b7bc-02d6afa4802a' # mia
    # api_key = '4028bf8f-8e98-4729-8b77-3e981b2d3e83' # Andre
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical?symbol={symbol}&convert=EUR&time_start={date}&time_end={date}&count=1'

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    # Estrai il prezzo storico dalla risposta
    historical_price = None
    if 'data' in data and symbol in data['data']:
        historical_price = data['data'][symbol]['quote']['EUR']['price']

    return historical_price
    '''

import requests
import datetime
import logging
import csv
from io import StringIO

def get_EURUSD_exchange_rate(data, attempts=5):
    """
    Ottiene il tasso di cambio EUR/USD per una data specifica (1 EUR = X USD).

    Args:
        data (datetime.date): La data per la quale si desidera ottenere il tasso di cambio.
        attempts (int): Numero massimo di giorni precedenti da provare.

    Returns:
        float or None: Il tasso di cambio EUR/USD per la data specificata, o None se non disponibile.
    """
    ref_date = data.strftime("%Y-%m-%d")
    url = f"https://tassidicambio.bancaditalia.it/terzevalute-wf-web/rest/v1.0/dailyRates?referenceDate={ref_date}&baseCurrencyIsoCode=USD&currencyIsoCode=EUR"  # Nota il '&'

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Log della risposta grezza
        logging.debug(f"Risposta grezza per {ref_date}: {response.text}")
        
        # Parse come CSV
        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            eur_usd_rate = float(row["Quotazione"])  # 1 EUR = X USD
            logging.debug(f"Tasso di cambio EUR/USD per {ref_date}: {eur_usd_rate:.6f}")
            return eur_usd_rate

    except requests.exceptions.RequestException as e:
        logging.error(f"Errore nella richiesta del tasso di cambio EUR/USD per {ref_date}: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Errore nel parsing del CSV per {ref_date}: {e}")

    # Fallback al giorno precedente con limite
    if attempts > 0:
        previous_day = data - datetime.timedelta(days=1)
        logging.debug(f"Tasso non trovato per {ref_date}, provo il giorno precedente: {previous_day.strftime('%Y-%m-%d')}")
        return get_EURUSD_exchange_rate(previous_day, attempts - 1)
    else:
        logging.error(f"Impossibile ottenere il tasso EUR/USD dopo {attempts} tentativi")
        return None