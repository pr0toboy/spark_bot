import csv
import hashlib
import hmac as _hmac
import sqlite3
import struct
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ecdsa import SECP256k1 as _CURVE
from ecdsa.ellipticcurve import PointJacobi as _PJ

from context import get_conn
from result import Result

# ── Constantes ────────────────────────────────────────────────────────────────

_CG       = "https://api.coingecko.com/api/v3"
_HDR      = {"Accept": "application/json", "User-Agent": "SparkBot/1.0"}
_JSON_HDR = {**_HDR, "Content-Type": "application/json"}

_B58  = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BC32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

_IDS = {
    "btc": "bitcoin",    "eth": "ethereum",    "sol": "solana",
    "bnb": "binancecoin","xrp": "ripple",      "ada": "cardano",
    "doge": "dogecoin",  "dot": "polkadot",    "avax": "avalanche-2",
    "matic": "matic-network", "link": "chainlink", "ltc": "litecoin",
    "uni": "uniswap",    "atom": "cosmos",     "near": "near",
    "trx": "tron",       "shib": "shiba-inu",  "pepe": "pepe",
    "op": "optimism",    "arb": "arbitrum",    "sui": "sui", "apt": "aptos",
}
_CHAIN_COIN   = {"btc": "bitcoin", "xpub": "bitcoin", "eth": "ethereum",
                 "avax": "avalanche-2", "sol": "solana", "dot": "polkadot"}
_CHAIN_SYM    = {"btc": "₿", "xpub": "₿", "eth": "Ξ",
                 "avax": "▲", "sol": "◎", "dot": "●"}
_CHAIN_TICKER = {"btc": "BTC", "xpub": "BTC", "eth": "ETH",
                 "avax": "AVAX", "sol": "SOL", "dot": "DOT"}
_TICKER_CHAIN = {
    "BTC": "xpub", "ETH": "eth", "MATIC": "eth", "BNB": "eth", "OP": "eth",
    "AVAX": "avax", "SOL": "sol", "DOT": "dot",
}

_SOL_RPC   = "https://api.mainnet-beta.solana.com"
_STAKE_PRG = "Stake11111111111111111111111111111111111111"

# One-time DB migration flag (reset on process restart, migrations are idempotent)
_DB_READY = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cg_id(coin: str) -> str:
    return _IDS.get(coin.lower(), coin.lower())

def _fmt(usd: float) -> str:
    if usd == 0:      return "$0.00"
    if usd >= 1:      return f"${usd:,.2f}"
    if usd >= 0.0001: return f"${usd:.6f}"
    return f"${usd:.2e}"

def _b58_decode(s: str) -> bytes:
    n = 0
    for c in s: n = n * 58 + _B58.index(c)
    leading = len(s) - len(s.lstrip("1"))
    return b"\x00" * leading + n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")


# ── DB ────────────────────────────────────────────────────────────────────────

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
        # Drop old CHECK constraint on chain column (one-shot)
        row = c.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='crypto_wallets'"
        ).fetchone()
        if row and "CHECK" in row[0]:
            c.execute("ALTER TABLE crypto_wallets RENAME TO _cw_old")
            c.execute("""CREATE TABLE crypto_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                chain TEXT NOT NULL)""")
            c.execute("INSERT INTO crypto_wallets SELECT * FROM _cw_old")
            c.execute("DROP TABLE _cw_old")
        # Migrate AVAX wallets imported as 'eth'
        c.execute("""UPDATE crypto_wallets SET chain='avax'
                     WHERE chain='eth'
                     AND (LOWER(label) LIKE '%avalanche%' OR LOWER(label) LIKE '%avax%')""")
        _DB_READY = True
    c.commit()
    return c


# ── Prix ──────────────────────────────────────────────────────────────────────

def _prices(coin_ids: list[str]) -> dict[str, dict]:
    if not coin_ids:
        return {}
    try:
        r = requests.get(f"{_CG}/simple/price", headers=_HDR, timeout=8, params={
            "ids": ",".join(coin_ids), "vs_currencies": "usd",
            "include_24hr_change": "true", "include_market_cap": "true",
        })
        return r.json()
    except Exception:
        return {}

def _price_one(coin_id: str) -> dict | None:
    return _prices([coin_id]).get(coin_id)


# ── Balances BTC ──────────────────────────────────────────────────────────────

def _btc_balance(addr: str) -> float | None:
    try:
        r = requests.get(f"https://blockchain.info/q/addressbalance/{addr}", timeout=8)
        return int(r.text.strip()) / 1e8
    except Exception:
        return None

def _bech32_polymod(vals: list) -> int:
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in vals:
        b = chk >> 25; chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1: chk ^= GEN[i]
    return chk

def _convertbits(data: bytes, fb: int, tb: int) -> list:
    acc, bits, ret = 0, 0, []
    for v in data:
        acc = ((acc << fb) | v) & 0x3FFFFFFF; bits += fb
        while bits >= tb:
            bits -= tb; ret.append((acc >> bits) & ((1 << tb) - 1))
    if bits: ret.append((acc << (tb - bits)) & ((1 << tb) - 1))
    return ret

def _p2wpkh_address(pubkey: bytes) -> str:
    h160 = hashlib.new("ripemd160", hashlib.sha256(pubkey).digest()).digest()
    data = [0] + _convertbits(h160, 8, 5)
    hrp  = "bc"
    pre  = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    chk  = _bech32_polymod(pre + data + [0] * 6) ^ 1
    return hrp + "1" + "".join(_BC32[d] for d in data) + \
           "".join(_BC32[(chk >> (5 * (5 - i))) & 31] for i in range(6))

def _ckd_pub(chaincode: bytes, pubkey: bytes, index: int) -> tuple[bytes, bytes]:
    h  = _hmac.new(chaincode, pubkey + struct.pack(">I", index), hashlib.sha512).digest()
    il, ir = int.from_bytes(h[:32], "big"), h[32:]
    G  = _CURVE.generator
    c  = _CURVE.curve
    p  = c.p()
    pf, px = pubkey[0], int.from_bytes(pubkey[1:], "big")
    y2 = (pow(px, 3, p) + c.a() * px + c.b()) % p
    py = pow(y2, (p + 1) // 4, p)
    if (py % 2) != (pf - 2): py = p - py
    pt = il * G + _PJ(c, px, py, 1)
    cx, cy = int(pt.x()), int(pt.y())
    return ir, bytes([2 if cy % 2 == 0 else 3]) + cx.to_bytes(32, "big")

def _btc_xpub_balance(xpub: str) -> float | None:
    try:
        raw  = _b58_decode(xpub)[4:-4]   # strip 4-byte version + 4-byte checksum
        cc, pk = raw[9:41], raw[41:]
        total = 0.0
        GAP   = 10  # BIP44 gap limit
        for branch in (0, 1):
            bcc, bpk = _ckd_pub(cc, pk, branch)
            gap = 0
            for i in range(50):
                _, cpk = _ckd_pub(bcc, bpk, i)
                r = requests.get(f"https://mempool.space/api/address/{_p2wpkh_address(cpk)}",
                                 headers=_HDR, timeout=8)
                if r.status_code != 200:
                    gap += 1
                    if gap >= GAP: break
                    continue
                cs  = r.json().get("chain_stats", {})
                total += (cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)) / 1e8
                gap = 0 if cs.get("tx_count", 0) else gap + 1
                if gap >= GAP: break
        return total
    except Exception:
        return None


# ── Balances ETH / AVAX ───────────────────────────────────────────────────────

def _eth_balance(addr: str) -> float | None:
    try:
        r = requests.get(f"https://eth.blockscout.com/api/v2/addresses/{addr}",
                         headers=_HDR, timeout=8)
        return int(r.json()["coin_balance"]) / 1e18 if r.status_code == 200 else None
    except Exception:
        return None

def _avax_balance(addr: str) -> float | None:
    try:
        r = requests.post("https://api.avax.network/ext/bc/C/rpc",
            json={"jsonrpc": "2.0", "id": 1,
                  "method": "eth_getBalance", "params": [addr, "latest"]},
            headers=_JSON_HDR, timeout=8)
        return int(r.json()["result"], 16) / 1e18
    except Exception:
        return None


# ── Balance SOL (liquid + staké) ──────────────────────────────────────────────

def _sol_rpc(method: str, params: list) -> dict:
    r = requests.post(_SOL_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        headers=_JSON_HDR, timeout=10)
    return r.json()

def _sol_balance(addr: str) -> float | None:
    try:
        liquid = _sol_rpc("getBalance", [addr])["result"]["value"] / 1e9
        sigs   = [s["signature"] for s in
                  _sol_rpc("getSignaturesForAddress", [addr, {"limit": 50}]).get("result", [])]
        candidates: set[str] = set()
        for sig in sigs:
            tx = _sol_rpc("getTransaction",
                          [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}]).get("result")
            if not tx or _STAKE_PRG not in tx["transaction"]["message"]["accountKeys"]:
                continue
            meta = tx["meta"]
            for i, acc in enumerate(tx["transaction"]["message"]["accountKeys"]):
                if acc in (addr, _STAKE_PRG): continue
                if meta["postBalances"][i] >= 500_000_000:
                    candidates.add(acc)
        staked = 0.0
        for acc in candidates:
            v = _sol_rpc("getAccountInfo", [acc, {"encoding": "base64"}]).get("result", {}).get("value")
            if v and v.get("owner") == _STAKE_PRG:
                staked += v["lamports"] / 1e9
        return liquid + staked
    except Exception:
        return None


# ── Balance DOT ───────────────────────────────────────────────────────────────

def _dot_balance(addr: str) -> float | None:
    try:
        raw    = _b58_decode(addr)
        pubkey = raw[1:33]                 # SS58: 1-byte prefix + 32-byte pubkey + 2-byte checksum
        TW     = "26aa394eea5630e07c48ae0c9558cef7b99d880ec681799c0cf30e8886371da9"
        key    = "0x" + TW + hashlib.blake2b(pubkey, digest_size=16).digest().hex() + pubkey.hex()
        r = requests.post("https://rpc.polkadot.io",
            json={"jsonrpc": "2.0", "id": 1, "method": "state_getStorage", "params": [key]},
            headers=_JSON_HDR, timeout=8)
        result = r.json().get("result")
        if not result:
            return 0.0
        raw_data = bytes.fromhex(result[2:])
        return int.from_bytes(raw_data[16:32], "little") / 1e10   # 1 DOT = 10^10 Planck
    except Exception:
        return None


# ── Dispatch ──────────────────────────────────────────────────────────────────

def _get_balance(addr: str, chain: str) -> float | None:
    return {
        "btc":  _btc_balance,
        "xpub": _btc_xpub_balance,
        "eth":  _eth_balance,
        "avax": _avax_balance,
        "sol":  _sol_balance,
        "dot":  _dot_balance,
    }.get(chain, lambda _: None)(addr)

def _detect_chain(addr: str) -> str | None:
    a = addr.strip()
    if a.startswith("xpub"):                        return "xpub"
    if a.lower().startswith("0x") and len(a) == 42: return "eth"
    if a.startswith("bc1") and len(a) <= 74:        return "btc"
    if a.startswith(("1", "3")) and len(a) <= 34:   return "btc"
    if 43 <= len(a) <= 44:                          return "sol"
    if a.startswith("1") and 46 <= len(a) <= 50:    return "dot"
    return None


# ── Rendu wallet ──────────────────────────────────────────────────────────────

def _wallet_line(label: str, address: str, chain: str, cache: dict, bal: float | None) -> str:
    short = address[:8] + "…" + address[-4:]
    sym   = _CHAIN_SYM.get(chain, "?")
    p     = cache.get(_CHAIN_COIN.get(chain, ""), {})
    dec   = 6 if chain in ("btc", "xpub") else 4
    bal_s = f"{bal:.{dec}f} {_CHAIN_TICKER.get(chain, chain.upper())}" \
            if bal is not None else "⚠ indisponible"
    if bal is not None and p.get("usd"):
        return f"  {sym}  {label} ({short}) — {bal_s} ≈ {_fmt(bal * p['usd'])}"
    return f"  {sym}  {label} ({short}) — {bal_s}"

def _fetch_wallets(rows: list) -> tuple[dict, dict]:
    """Fetch prices and balances in parallel. Returns (price_cache, {(addr,chain): bal})."""
    needed = list({_CHAIN_COIN[ch] for _, _, ch in rows if ch in _CHAIN_COIN})
    with ThreadPoolExecutor(max_workers=len(rows) + 1) as ex:
        price_fut = ex.submit(_prices, needed)
        bal_futs  = {(a, ch): ex.submit(_get_balance, a, ch) for _, a, ch in rows}
        cache = price_fut.result()
        bals  = {k: f.result() for k, f in bal_futs.items()}
    return cache, bals


# ── Sous-commandes ────────────────────────────────────────────────────────────

def _cmd_price(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto price <coin>  (ex: btc, eth, sol)")
    coin = args[0].lower()
    print(f"📡 Prix {coin.upper()}…")
    d = _price_one(_cg_id(coin))
    if not d:
        return Result.error(f"❌ Coin « {coin} » introuvable.")
    chg  = d.get("usd_24h_change") or 0
    mc   = d.get("usd_market_cap") or 0
    mc_s = f"${mc/1e9:.2f}B" if mc >= 1e9 else f"${mc/1e6:.2f}M"
    return Result.success(
        f"💰 {coin.upper()}\n"
        f"   Prix : {_fmt(d['usd'])}\n"
        f"   24h  : {'▲' if chg >= 0 else '▼'} {chg:+.2f}%\n"
        f"   Cap  : {mc_s}"
    )


def _cmd_news() -> Result:
    print("📰 Tendances…")
    try:
        coins = requests.get(f"{_CG}/search/trending", headers=_HDR, timeout=8).json().get("coins", [])
        if not coins:
            return Result.error("❌ API indisponible.")
        lines = ["🔥 Tendances CoinGecko :"]
        for item in coins[:7]:
            c = item["item"]
            lines.append(f"  #{str(c.get('market_cap_rank','–')):>4}  {c['symbol'].upper():<6} — {c['name']}")
        try:
            g   = requests.get(f"{_CG}/global", headers=_HDR, timeout=5).json().get("data", {})
            mc  = g.get("total_market_cap", {}).get("usd", 0)
            dom = g.get("market_cap_percentage", {}).get("btc", 0)
            lines += ["", f"🌍 Marché : ${mc/1e12:.2f}T  |  BTC dominance : {dom:.1f}%"]
        except Exception:
            pass
        return Result.success("\n".join(lines))
    except Exception:
        return Result.error("❌ API CoinGecko indisponible.")


def _cmd_wallet_add(args: list) -> Result:
    if len(args) < 2:
        return Result.error("Usage : /crypto wallet add <adresse> <label>")
    address, label = args[0], " ".join(args[1:])
    chain = _detect_chain(address)
    if not chain:
        return Result.error("❌ Adresse non reconnue (BTC/xpub, ETH 0x…, SOL 44c, DOT 48c).")
    c = _conn()
    try:
        c.execute("INSERT INTO crypto_wallets (label,address,chain) VALUES (?,?,?)",
                  (label, address, chain))
        c.commit()
    except sqlite3.IntegrityError:
        c.close(); return Result.error(f"❌ Label « {label} » déjà utilisé.")
    c.close()
    return Result.success(f"{_CHAIN_SYM.get(chain, chain.upper())}  Wallet « {label} » ({chain.upper()}) ajouté.")


def _cmd_wallet_list() -> Result:
    c = _conn()
    rows = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucun wallet — /crypto wallet add <adresse> <label>")
    print("🔍 Balances…")
    cache, bals = _fetch_wallets(rows)
    lines = [f"💼 Portfolio ({len(rows)}) :"] + [
        _wallet_line(l, a, ch, cache, bals[(a, ch)]) for l, a, ch in rows
    ]
    return Result.success("\n".join(lines))


def _cmd_wallet_remove(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto wallet remove <label>")
    label = " ".join(args)
    c     = _conn()
    cur   = c.execute("DELETE FROM crypto_wallets WHERE label=?", (label,))
    c.commit(); c.close()
    return Result.success(f"🗑️  Wallet « {label} » supprimé.") if cur.rowcount \
        else Result.error(f"❌ Wallet « {label} » introuvable.")


def _cmd_import(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto import <fichier.csv>")
    path = Path(" ".join(args))
    if not path.exists():
        return Result.error(f"❌ Fichier introuvable : {path}")

    seen: dict[str, tuple[str, str]] = {}
    skipped: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr   = row["Account xpub"].strip()
            name   = row["Account Name"].strip()
            ticker = row["Currency Ticker"].strip().upper()
            if addr in seen: continue
            chain = _TICKER_CHAIN.get(ticker)
            if chain is None:
                skipped.add(ticker); continue
            if ticker == "BTC" and not addr.startswith("xpub"):
                chain = "btc"
            seen[addr] = (name, chain)

    if not seen:
        return Result.error("❌ Aucun compte reconnu dans le fichier.")

    c = _conn()
    added, dupes = [], []
    for address, (label, chain) in seen.items():
        try:
            c.execute("INSERT INTO crypto_wallets (label,address,chain) VALUES (?,?,?)",
                      (label, address, chain))
            added.append(f"  ✓ {_CHAIN_SYM.get(chain, chain.upper())}  {label} ({chain.upper()})")
        except sqlite3.IntegrityError:
            dupes.append(f"  ⚠ {label} — déjà présent")
    c.commit(); c.close()

    lines = [f"📥 Import Ledger : {len(added)} ajouté(s), {len(dupes)} ignoré(s)"]
    lines += added + dupes
    if skipped:
        lines.append(f"  ℹ tickers ignorés : {', '.join(sorted(skipped))}")
    lines.append("\nTape /crypto pour voir les balances.")
    return Result.success("\n".join(lines))


def _cmd_alert_add(args: list) -> Result:
    if len(args) < 3:
        return Result.error("Usage : /crypto alert add <coin> <above|below> <prix>")
    coin, direction = args[0].lower(), args[1].lower()
    if direction not in ("above", "below"):
        return Result.error("❌ Direction : above ou below.")
    try:
        price = float(args[2].replace(",", ""))
    except ValueError:
        return Result.error(f"❌ Prix invalide : {args[2]}")
    c  = _conn()
    c.execute("INSERT INTO crypto_alerts (coin,direction,price) VALUES (?,?,?)",
              (_cg_id(coin), direction, price))
    c.commit()
    aid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return Result.success(
        f"🔔 Alerte #{aid} : {coin.upper()} "
        f"{'au-dessus de' if direction == 'above' else 'en-dessous de'} {_fmt(price)}"
    )


def _cmd_alert_list() -> Result:
    c    = _conn()
    rows = c.execute("SELECT id,coin,direction,price,active FROM crypto_alerts ORDER BY id").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucune alerte — /crypto alert add <coin> <above|below> <prix>")
    lines = ["🔔 Alertes prix :"]
    for aid, coin, direction, price, active in rows:
        lines.append(
            f"  {'✅' if active else '⛔'} #{aid}  "
            f"{coin.upper()} {'>' if direction == 'above' else '<'} {_fmt(price)}"
        )
    return Result.success("\n".join(lines))


def _cmd_alert_remove(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto alert remove <id>")
    try:
        aid = int(args[0])
    except ValueError:
        return Result.error(f"❌ ID invalide : {args[0]}")
    c   = _conn()
    cur = c.execute("DELETE FROM crypto_alerts WHERE id=?", (aid,))
    c.commit(); c.close()
    return Result.success(f"🗑️  Alerte #{aid} supprimée.") if cur.rowcount \
        else Result.error(f"❌ Alerte #{aid} introuvable.")


def _cmd_alert_check() -> Result:
    c    = _conn()
    rows = c.execute("SELECT id,coin,direction,price FROM crypto_alerts WHERE active=1").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucune alerte active.")
    print("📡 Vérification des alertes…")
    live = _prices(list({r[1] for r in rows}))
    triggered, waiting = [], []
    c = _conn()
    for aid, coin, direction, target in rows:
        cur_price = (live.get(coin) or {}).get("usd")
        if cur_price is None:
            waiting.append(f"  ⚠  #{aid} {coin.upper()} — prix indisponible")
            continue
        op   = ">" if direction == "above" else "<"
        line = f"  #{aid}  {coin.upper()} {_fmt(cur_price)} {op} {_fmt(target)}"
        hit  = (direction == "above" and cur_price >= target) or \
               (direction == "below" and cur_price <= target)
        if hit:
            c.execute("UPDATE crypto_alerts SET active=0 WHERE id=?", (aid,))
            triggered.append(f"🚨 {line}  ← DÉCLENCHÉE")
        else:
            waiting.append(f"  ✓ {line}")
    c.commit(); c.close()
    out = []
    if triggered: out += ["🚨 Déclenchées :"] + triggered
    if waiting:   out += ["📊 En attente :"] + waiting
    return Result.success("\n".join(out))


def _cmd_portfolio() -> Result:
    c        = _conn()
    wallets  = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    n_alerts = c.execute("SELECT COUNT(*) FROM crypto_alerts WHERE active=1").fetchone()[0]
    c.close()

    lines = ["📊 Résumé crypto :"]

    if wallets:
        print("🔍 Balances…")
        cache, bals = _fetch_wallets(wallets)
        lines += ["", f"💼 Wallets ({len(wallets)}) :"] + [
            _wallet_line(l, a, ch, cache, bals[(a, ch)]) for l, a, ch in wallets
        ]
    else:
        lines.append("  Aucun wallet — /crypto wallet add <adresse> <label>")

    print("📡 Prix…")
    top  = ["bitcoin", "ethereum", "avalanche-2", "solana", "polkadot"]
    mkt  = _prices(top)
    lines += ["", "💹 Marché :"]
    for sym, cid in [("BTC","bitcoin"),("ETH","ethereum"),("AVAX","avalanche-2"),
                     ("SOL","solana"),("DOT","polkadot")]:
        d = mkt.get(cid)
        if d:
            chg = d.get("usd_24h_change") or 0
            lines.append(f"  {sym:<4} {_fmt(d['usd'])}  {'▲' if chg >= 0 else '▼'} {chg:+.2f}%")

    if n_alerts:
        lines += ["", f"🔔 {n_alerts} alerte(s) active(s) — /crypto alert check"]

    return Result.success("\n".join(lines))


# ── Handler principal ─────────────────────────────────────────────────────────

def handle(ctx, user_input: str) -> Result:
    parts = user_input.removeprefix("/crypto").strip().split()
    if not parts:
        return _cmd_portfolio()

    sub = parts[0].lower()
    if sub == "price":  return _cmd_price(parts[1:])
    if sub == "news":   return _cmd_news()
    if sub == "import": return _cmd_import(parts[1:])

    if sub == "wallet":
        action = parts[1].lower() if len(parts) > 1 else ""
        if action == "add":    return _cmd_wallet_add(parts[2:])
        if action == "list":   return _cmd_wallet_list()
        if action == "remove": return _cmd_wallet_remove(parts[2:])
        return Result.error("Sous-commandes wallet : add <adresse> <label> | list | remove <label>")

    if sub == "alert":
        action = parts[1].lower() if len(parts) > 1 else ""
        if action == "add":    return _cmd_alert_add(parts[2:])
        if action == "list":   return _cmd_alert_list()
        if action == "remove": return _cmd_alert_remove(parts[2:])
        if action == "check":  return _cmd_alert_check()
        return Result.error("Sous-commandes alert : add <coin> <above|below> <prix> | list | remove <id> | check")

    return Result.error(f"Sous-commande « {sub} » inconnue. Tape /help crypto.")
