import sqlite3
import requests
from fastapi import APIRouter, HTTPException
from app.models import (
    CryptoWalletItem, CryptoWalletCreate, CryptoPortfolio,
    CryptoAlertItem, CryptoAlertCreate, CryptoPriceItem,
    CryptoTrendItem, CryptoMarketItem,
)
from commands.crypto import (
    _conn, _prices, _price_one, _cg_id, _fetch_wallets,
    _CHAIN_COIN, _detect_chain, _HDR, _CG,
)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])

_TOP_COINS = [
    ("BTC",  "bitcoin"),
    ("ETH",  "ethereum"),
    ("SOL",  "solana"),
    ("AVAX", "avalanche-2"),
    ("BNB",  "binancecoin"),
    ("XRP",  "ripple"),
    ("ADA",  "cardano"),
    ("DOT",  "polkadot"),
]


@router.get("/market", response_model=list[CryptoMarketItem])
def get_market():
    mkt = _prices([cid for _, cid in _TOP_COINS])
    return [
        CryptoMarketItem(
            symbol=sym,
            price_usd=d.get("usd", 0),
            change_24h=d.get("usd_24h_change") or 0,
        )
        for sym, cid in _TOP_COINS
        if (d := mkt.get(cid))
    ]


@router.get("/trending", response_model=list[CryptoTrendItem])
def get_trending():
    try:
        r = requests.get(f"{_CG}/search/trending", headers=_HDR, timeout=8)
        coins = r.json().get("coins", [])
        return [
            CryptoTrendItem(
                rank=item["item"].get("market_cap_rank"),
                symbol=item["item"]["symbol"].upper(),
                name=item["item"]["name"],
            )
            for item in coins[:7]
        ]
    except Exception:
        raise HTTPException(status_code=503, detail="API CoinGecko indisponible.")


@router.get("/wallets", response_model=list[CryptoWalletItem])
def list_wallets():
    c = _conn()
    rows = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    c.close()
    return [CryptoWalletItem(label=r[0], address=r[1], chain=r[2]) for r in rows]


@router.post("/wallets", response_model=CryptoWalletItem)
def add_wallet(req: CryptoWalletCreate):
    chain = _detect_chain(req.address)
    if not chain:
        raise HTTPException(status_code=400, detail="Adresse non reconnue (BTC/xpub, ETH 0x…, SOL, DOT).")
    c = _conn()
    try:
        c.execute("INSERT INTO crypto_wallets (label,address,chain) VALUES (?,?,?)",
                  (req.label, req.address, chain))
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        raise HTTPException(status_code=409, detail=f"Label « {req.label} » déjà utilisé.")
    c.close()
    return CryptoWalletItem(label=req.label, address=req.address, chain=chain)


@router.delete("/wallets/{label}")
def remove_wallet(label: str):
    c = _conn()
    cur = c.execute("DELETE FROM crypto_wallets WHERE label=?", (label,))
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Wallet « {label} » introuvable.")
    return {"ok": True}


@router.get("/portfolio", response_model=CryptoPortfolio)
def get_portfolio():
    c = _conn()
    wallet_rows = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    c.close()

    wallets: list[CryptoWalletItem] = []
    total_usd = 0.0
    price_cache: dict = {}

    if wallet_rows:
        price_cache, bals = _fetch_wallets(wallet_rows)
        for label, address, chain in wallet_rows:
            bal = bals.get((address, chain))
            bal_usd: float | None = None
            if bal is not None:
                p = price_cache.get(_CHAIN_COIN.get(chain, ""), {})
                if p.get("usd"):
                    bal_usd = bal * p["usd"]
                    total_usd += bal_usd
            wallets.append(CryptoWalletItem(
                label=label, address=address, chain=chain,
                balance=bal, balance_usd=bal_usd,
            ))

    # Reuse wallet price cache; only fetch top coins not already loaded
    top_ids = [cid for _, cid in _TOP_COINS]
    missing = [cid for cid in top_ids if cid not in price_cache]
    if missing:
        price_cache.update(_prices(missing))

    market = [
        CryptoMarketItem(
            symbol=sym,
            price_usd=d.get("usd", 0),
            change_24h=d.get("usd_24h_change") or 0,
        )
        for sym, cid in _TOP_COINS
        if (d := price_cache.get(cid))
    ]

    return CryptoPortfolio(
        wallets=wallets,
        market=market,
        total_usd=total_usd if wallet_rows else None,
    )


@router.get("/price/{coin}", response_model=CryptoPriceItem)
def get_price(coin: str):
    d = _price_one(_cg_id(coin.lower()))
    if not d:
        raise HTTPException(status_code=404, detail=f"Coin « {coin} » introuvable.")
    return CryptoPriceItem(
        symbol=coin.upper(),
        price_usd=d.get("usd", 0),
        change_24h=d.get("usd_24h_change") or 0,
        market_cap=d.get("usd_market_cap"),
    )


@router.get("/alerts", response_model=list[CryptoAlertItem])
def list_alerts():
    c = _conn()
    rows = c.execute(
        "SELECT id,coin,direction,price,active FROM crypto_alerts ORDER BY id"
    ).fetchall()
    c.close()
    return [
        CryptoAlertItem(id=r[0], coin=r[1], direction=r[2], price=r[3], active=bool(r[4]))
        for r in rows
    ]


@router.post("/alerts", response_model=CryptoAlertItem)
def add_alert(req: CryptoAlertCreate):
    if req.direction not in ("above", "below"):
        raise HTTPException(status_code=400, detail="Direction : above ou below.")
    coin_id = _cg_id(req.coin.lower())
    c = _conn()
    c.execute("INSERT INTO crypto_alerts (coin,direction,price) VALUES (?,?,?)",
              (coin_id, req.direction, req.price))
    c.commit()
    aid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return CryptoAlertItem(id=aid, coin=coin_id, direction=req.direction, price=req.price, active=True)


@router.delete("/alerts/{alert_id}")
def remove_alert(alert_id: int):
    c = _conn()
    cur = c.execute("DELETE FROM crypto_alerts WHERE id=?", (alert_id,))
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Alerte #{alert_id} introuvable.")
    return {"ok": True}
