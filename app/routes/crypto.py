import hashlib
import hmac as _hmac
import json
import os
import sqlite3
import struct
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException
from app.models import (
    CryptoWalletItem, CryptoWalletCreate, CryptoWalletRename, CryptoPortfolio,
    CryptoAlertItem, CryptoAlertCreate, CryptoPriceItem,
    CryptoTrendItem, CryptoMarketItem,
)
from app.context import get_conn

from ecdsa import SECP256k1 as _CURVE
from ecdsa.ellipticcurve import PointJacobi as _PJ

_CG  = "https://api.coingecko.com/api/v3"
_HDR = {"Accept": "application/json", "User-Agent": "SparkBot/1.0"}
_JSON_HDR = {**_HDR, "Content-Type": "application/json"}

_B58  = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BC32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "bnb": "binancecoin", "xrp": "ripple", "ada": "cardano",
    "doge": "dogecoin", "dot": "polkadot", "avax": "avalanche-2",
    "matic": "matic-network", "link": "chainlink", "ltc": "litecoin",
    "uni": "uniswap", "atom": "cosmos", "near": "near",
    "trx": "tron", "shib": "shiba-inu", "pepe": "pepe",
    "op": "optimism", "arb": "arbitrum", "sui": "sui", "apt": "aptos",
}
_CHAIN_COIN   = {"btc": "bitcoin", "xpub": "bitcoin", "eth": "ethereum",
                 "avax": "avalanche-2", "sol": "solana", "dot": "polkadot",
                 "arb": "ethereum", "hl": "usd-coin"}
_CHAIN_SYM    = {"btc": "₿", "xpub": "₿", "eth": "Ξ", "avax": "▲", "sol": "◎", "dot": "●",
                 "arb": "Ξ", "hl": "$"}
_CHAIN_TICKER = {"btc": "BTC", "xpub": "BTC", "eth": "ETH", "avax": "AVAX", "sol": "SOL", "dot": "DOT",
                 "arb": "ETH", "hl": "USDC"}

_SOL_RPC   = "https://api.mainnet-beta.solana.com"
_STAKE_PRG = "Stake11111111111111111111111111111111111111"

_DB_READY = False
_PRICE_CACHE: dict = {}
_PRICE_TTL = 60
_EUR_USD_RATE: float = 0.92  # fallback, updated whenever CoinGecko returns EUR prices

def _load_wallets() -> list[tuple[str, str, str]]:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "wallets.json")
    try:
        with open(os.path.normpath(path)) as f:
            return [(w["label"], w["address"], w["chain"]) for w in json.load(f)]
    except FileNotFoundError:
        return []


def _cg_id(coin: str) -> str:
    return _IDS.get(coin.lower(), coin.lower())


def _b58_decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + _B58.index(c)
    leading = len(s) - len(s.lstrip("1"))
    return b"\x00" * leading + n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")


def _conn():
    global _DB_READY
    c = get_conn()
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        chain TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT NOT NULL,
        direction TEXT NOT NULL CHECK(direction IN ('above','below')),
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1)""")
    if not _DB_READY:
        row = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='crypto_wallets'").fetchone()
        if row and "CHECK" in row[0]:
            c.execute("ALTER TABLE crypto_wallets RENAME TO _cw_old")
            c.execute("""CREATE TABLE crypto_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                chain TEXT NOT NULL)""")
            c.execute("INSERT INTO crypto_wallets SELECT * FROM _cw_old")
            c.execute("DROP TABLE _cw_old")
        c.execute("""UPDATE crypto_wallets SET chain='avax'
                     WHERE chain='eth'
                     AND (LOWER(label) LIKE '%avalanche%' OR LOWER(label) LIKE '%avax%')""")
        for label, addr, chain in _load_wallets():
            c.execute("INSERT OR IGNORE INTO crypto_wallets (label,address,chain) VALUES (?,?,?)",
                      (label, addr, chain))
        c.execute("UPDATE crypto_wallets SET chain='arb' WHERE label='Rabby' AND chain='eth'")
        c.execute("""INSERT OR IGNORE INTO crypto_wallets (label,address,chain)
                     SELECT 'Hyperliquid', address, 'hl' FROM crypto_wallets WHERE label='Rabby'""")
        _DB_READY = True
    c.commit()
    return c


def _prices(coin_ids: list[str]) -> dict[str, dict]:
    global _EUR_USD_RATE
    if not coin_ids:
        return {}
    key = frozenset(coin_ids)
    cached = _PRICE_CACHE.get(key)
    if cached and time.time() - cached[0] < _PRICE_TTL:
        return cached[1]
    try:
        r = requests.get(f"{_CG}/simple/price", headers=_HDR, timeout=8, params={
            "ids": ",".join(coin_ids), "vs_currencies": "usd,eur",
            "include_24hr_change": "true", "include_market_cap": "true",
        })
        if r.status_code != 200:
            return {}
        data = r.json()
        # Update EUR/USD rate from any coin that has both usd and eur prices
        for d in data.values():
            if d.get("usd") and d.get("eur"):
                _EUR_USD_RATE = d["eur"] / d["usd"]
                break
        now = time.time()
        for k in [k for k, (ts, _) in _PRICE_CACHE.items() if now - ts >= _PRICE_TTL]:
            del _PRICE_CACHE[k]
        _PRICE_CACHE[key] = (now, data)
        return data
    except Exception:
        return {}


def _price_one(coin_id: str) -> dict | None:
    return _prices([coin_id]).get(coin_id)


def _btc_balance(addr: str) -> float | None:
    try:
        r = requests.get(f"https://mempool.space/api/address/{addr}", headers=_HDR, timeout=8)
        if r.status_code != 200:
            return None
        cs = r.json().get("chain_stats", {})
        return (cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)) / 1e8
    except Exception:
        return None


def _bech32_polymod(vals: list) -> int:
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in vals:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= GEN[i]
    return chk


def _convertbits(data: bytes, fb: int, tb: int) -> list:
    acc, bits, ret = 0, 0, []
    for v in data:
        acc = ((acc << fb) | v) & 0x3FFFFFFF
        bits += fb
        while bits >= tb:
            bits -= tb
            ret.append((acc >> bits) & ((1 << tb) - 1))
    if bits:
        ret.append((acc << (tb - bits)) & ((1 << tb) - 1))
    return ret


def _p2wpkh_address(pubkey: bytes) -> str:
    h160 = hashlib.new("ripemd160", hashlib.sha256(pubkey).digest()).digest()
    data = [0] + _convertbits(h160, 8, 5)
    hrp = "bc"
    pre = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    chk = _bech32_polymod(pre + data + [0] * 6) ^ 1
    return hrp + "1" + "".join(_BC32[d] for d in data) + \
           "".join(_BC32[(chk >> (5 * (5 - i))) & 31] for i in range(6))


def _ckd_pub(chaincode: bytes, pubkey: bytes, index: int) -> tuple[bytes, bytes]:
    h = _hmac.new(chaincode, pubkey + struct.pack(">I", index), hashlib.sha512).digest()
    il, ir = int.from_bytes(h[:32], "big"), h[32:]
    G = _CURVE.generator
    c = _CURVE.curve
    p = c.p()
    pf, px = pubkey[0], int.from_bytes(pubkey[1:], "big")
    y2 = (pow(px, 3, p) + c.a() * px + c.b()) % p
    py = pow(y2, (p + 1) // 4, p)
    if (py % 2) != (pf - 2):
        py = p - py
    pt = il * G + _PJ(c, px, py, 1)
    cx, cy = int(pt.x()), int(pt.y())
    return ir, bytes([2 if cy % 2 == 0 else 3]) + cx.to_bytes(32, "big")


def _btc_xpub_balance(xpub: str) -> float | None:
    try:
        # zpub/ypub have the same payload structure as xpub — only version bytes differ
        raw = _b58_decode(xpub)[4:-4]
        cc, pk = raw[9:41], raw[41:]
        total = 0.0
        GAP = 10
        for branch in (0, 1):
            bcc, bpk = _ckd_pub(cc, pk, branch)
            gap = 0
            for i in range(50):
                _, cpk = _ckd_pub(bcc, bpk, i)
                r = requests.get(f"https://mempool.space/api/address/{_p2wpkh_address(cpk)}",
                                 headers=_HDR, timeout=8)
                if r.status_code != 200:
                    gap += 1
                    if gap >= GAP:
                        break
                    continue
                cs = r.json().get("chain_stats", {})
                total += (cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)) / 1e8
                gap = 0 if cs.get("tx_count", 0) else gap + 1
                if gap >= GAP:
                    break
        return total
    except Exception:
        return None


def _eth_balance(addr: str) -> float | None:
    try:
        r = requests.get(f"https://eth.blockscout.com/api/v2/addresses/{addr}", headers=_HDR, timeout=8)
        return int(r.json()["coin_balance"]) / 1e18 if r.status_code == 200 else None
    except Exception:
        return None


def _arb_balance(addr: str) -> float | None:
    try:
        r = requests.post("https://arb1.arbitrum.io/rpc",
            json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [addr, "latest"]},
            headers=_JSON_HDR, timeout=8)
        return int(r.json()["result"], 16) / 1e18
    except Exception:
        return None


def _hl_balance(addr: str) -> float | None:
    try:
        r = requests.post("https://api.hyperliquid.xyz/info",
            json={"type": "clearinghouseState", "user": addr},
            headers=_JSON_HDR, timeout=8)
        perp = float(r.json().get("marginSummary", {}).get("accountValue", 0)) if r.status_code == 200 else 0.0
        r2 = requests.post("https://api.hyperliquid.xyz/info",
            json={"type": "spotClearinghouseState", "user": addr},
            headers=_JSON_HDR, timeout=8)
        spot = sum(float(b.get("total", 0)) for b in (r2.json().get("balances") or []) if r2.status_code == 200)
        return perp + spot
    except Exception:
        return None


def _avax_balance(addr: str) -> float | None:
    try:
        r = requests.post("https://api.avax.network/ext/bc/C/rpc",
            json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [addr, "latest"]},
            headers=_JSON_HDR, timeout=8)
        return int(r.json()["result"], 16) / 1e18
    except Exception:
        return None


def _sol_rpc(method: str, params: list) -> dict:
    r = requests.post(_SOL_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        headers=_JSON_HDR, timeout=10)
    return r.json()


def _sol_balance(addr: str) -> float | None:
    try:
        liquid = _sol_rpc("getBalance", [addr])["result"]["value"] / 1e9
        stake_resp = _sol_rpc("getProgramAccounts", [
            _STAKE_PRG,
            {"encoding": "base64", "filters": [
                {"dataSize": 200},
                {"memcmp": {"offset": 44, "bytes": addr}},
            ]},
        ])
        staked = sum(
            acc["account"]["lamports"] / 1e9
            for acc in (stake_resp.get("result") or [])
        )
        return liquid + staked
    except Exception:
        return None


def _dot_balance(addr: str) -> float | None:
    try:
        raw = _b58_decode(addr)
        pubkey = raw[1:33]
        TW = "26aa394eea5630e07c48ae0c9558cef7b99d880ec681799c0cf30e8886371da9"
        key = "0x" + TW + hashlib.blake2b(pubkey, digest_size=16).digest().hex() + pubkey.hex()
        r = requests.post("https://rpc.polkadot.io",
            json={"jsonrpc": "2.0", "id": 1, "method": "state_getStorage", "params": [key]},
            headers=_JSON_HDR, timeout=8)
        result = r.json().get("result")
        if not result:
            return 0.0
        raw_data = bytes.fromhex(result[2:])
        return int.from_bytes(raw_data[16:32], "little") / 1e10
    except Exception:
        return None


def _get_balance(addr: str, chain: str) -> float | None:
    return {
        "btc": _btc_balance, "xpub": _btc_xpub_balance,
        "eth": _eth_balance, "avax": _avax_balance,
        "sol": _sol_balance, "dot": _dot_balance,
        "arb": _arb_balance, "hl": _hl_balance,
    }.get(chain, lambda _: None)(addr)


def _detect_chain(addr: str) -> str | None:
    a = addr.strip()
    if a.startswith(("xpub", "zpub", "ypub")):        return "xpub"
    if a.lower().startswith("0x") and len(a) == 42:  return "eth"
    if a.startswith("bc1") and len(a) <= 74:         return "btc"
    if a.startswith(("1", "3")) and len(a) <= 34:    return "btc"
    if 43 <= len(a) <= 44:                           return "sol"
    if a.startswith("1") and 46 <= len(a) <= 50:     return "dot"
    return None

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
            price_eur=d.get("eur", 0.0),
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


@router.patch("/wallets/{label}", response_model=CryptoWalletItem)
def rename_wallet(label: str, req: CryptoWalletRename):
    c = _conn()
    row = c.execute("SELECT address, chain FROM crypto_wallets WHERE label=?", (label,)).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail=f"Wallet « {label} » introuvable.")
    try:
        c.execute("UPDATE crypto_wallets SET label=? WHERE label=?", (req.label, label))
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        raise HTTPException(status_code=409, detail=f"Label « {req.label} » déjà utilisé.")
    c.close()
    return CryptoWalletItem(label=req.label, address=row[0], chain=row[1])


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

    top_ids = [cid for _, cid in _TOP_COINS]
    wallet_coin_ids = list({_CHAIN_COIN[ch] for _, _, ch in wallet_rows if ch in _CHAIN_COIN})
    all_ids = list({*top_ids, *wallet_coin_ids})

    with ThreadPoolExecutor(max_workers=len(wallet_rows) + 1) as ex:
        price_fut = ex.submit(_prices, all_ids)
        bal_futs = {(a, ch): ex.submit(_get_balance, a, ch) for _, a, ch in wallet_rows}
        price_cache = price_fut.result()
        bals = {k: f.result() for k, f in bal_futs.items()}

    wallets: list[CryptoWalletItem] = []
    total_usd = 0.0
    total_eur = 0.0
    for label, address, chain in wallet_rows:
        bal = bals.get((address, chain))
        bal_usd: float | None = None
        bal_eur: float | None = None
        if bal is not None:
            p = price_cache.get(_CHAIN_COIN.get(chain, ""), {})
            if p.get("usd"):
                bal_usd = bal * p["usd"]
                total_usd += bal_usd
            eur_price = p.get("eur") or (p["usd"] * _EUR_USD_RATE if p.get("usd") else None)
            if eur_price:
                bal_eur = bal * eur_price
                total_eur += bal_eur
        wallets.append(CryptoWalletItem(
            label=label, address=address, chain=chain,
            balance=bal, balance_usd=bal_usd, balance_eur=bal_eur,
        ))

    market = [
        CryptoMarketItem(
            symbol=sym,
            price_usd=d.get("usd", 0),
            price_eur=d.get("eur", 0.0),
            change_24h=d.get("usd_24h_change") or 0,
        )
        for sym, cid in _TOP_COINS
        if (d := price_cache.get(cid))
    ]

    return CryptoPortfolio(
        wallets=wallets,
        market=market,
        total_usd=total_usd if (wallet_rows and total_usd > 0) else None,
        total_eur=total_eur if (wallet_rows and total_eur > 0) else None,
    )


@router.get("/price/{coin}", response_model=CryptoPriceItem)
def get_price(coin: str):
    d = _price_one(_cg_id(coin.lower()))
    if not d:
        raise HTTPException(status_code=404, detail=f"Coin « {coin} » introuvable.")
    return CryptoPriceItem(
        symbol=coin.upper(),
        price_usd=d.get("usd", 0),
        price_eur=d.get("eur", 0.0),
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
