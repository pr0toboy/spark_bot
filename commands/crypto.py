import csv
import sqlite3
import requests
from pathlib import Path
from context import get_conn
from result import Result

_CG  = "https://api.coingecko.com/api/v3"
_HDR = {"Accept": "application/json", "User-Agent": "SparkBot/1.0"}
_JSON_HDR = {**_HDR, "Content-Type": "application/json"}

_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
    "xrp": "ripple", "ada": "cardano", "doge": "dogecoin", "dot": "polkadot",
    "avax": "avalanche-2", "matic": "matic-network", "link": "chainlink",
    "ltc": "litecoin", "uni": "uniswap", "atom": "cosmos", "near": "near",
    "trx": "tron", "shib": "shiba-inu", "pepe": "pepe", "op": "optimism",
    "arb": "arbitrum", "sui": "sui", "apt": "aptos",
}

# chain → CoinGecko ID
_CHAIN_COIN = {
    "btc": "bitcoin", "xpub": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "dot": "polkadot",
}

# CSV ticker → chain (Ledger Live export)
_TICKER_CHAIN = {
    "BTC": "xpub",   # Ledger exports xpub for BTC
    "ETH": "eth", "AVAX": "eth", "MATIC": "eth", "BNB": "eth", "OP": "eth",
    "SOL": "sol",
    "DOT": "dot",
}

def _cg_id(coin: str) -> str:
    return _IDS.get(coin.lower(), coin.lower())

def _fmt(usd: float) -> str:
    if usd == 0:      return "$0.00"
    if usd >= 1:      return f"${usd:,.2f}"
    if usd >= 0.0001: return f"${usd:.6f}"
    return f"${usd:.2e}"

_CHAIN_SYM = {"btc": "₿", "xpub": "₿", "eth": "Ξ", "sol": "◎", "dot": "●"}


# ── DB ────────────────────────────────────────────────────────────────────────

def _conn():
    c = get_conn()
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        chain TEXT NOT NULL)""")
    # Migrate pre-existing table that had a restrictive CHECK constraint
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
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT NOT NULL,
        direction TEXT NOT NULL CHECK(direction IN ('above','below')),
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1)""")
    c.commit()
    return c


# ── Balances ──────────────────────────────────────────────────────────────────

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

def _btc_balance(addr: str) -> float | None:
    try:
        r = requests.get(f"https://blockchain.info/q/addressbalance/{addr}", timeout=8)
        return int(r.text.strip()) / 1e8
    except Exception:
        return None

def _btc_xpub_balance(xpub: str) -> float | None:
    # blockchain.info multiaddr supports xpub natively, free, no key
    try:
        r = requests.get(
            f"https://blockchain.info/multiaddr?active={xpub}",
            headers=_HDR, timeout=10,
        )
        return r.json()["wallet"]["final_balance"] / 1e8
    except Exception:
        return None

def _eth_balance(addr: str) -> float | None:
    # BlockScout public API — no key required
    try:
        r = requests.get(
            f"https://eth.blockscout.com/api/v2/addresses/{addr}",
            headers=_HDR, timeout=8,
        )
        return int(r.json()["coin_balance"]) / 1e18 if r.status_code == 200 else None
    except Exception:
        return None

def _sol_balance(addr: str) -> float | None:
    try:
        r = requests.post(
            "https://api.mainnet-beta.solana.com",
            json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [addr]},
            headers=_JSON_HDR, timeout=8,
        )
        return r.json()["result"]["value"] / 1e9
    except Exception:
        return None

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def _ss58_pubkey(addr: str) -> bytes:
    """Decode SS58 address → 32-byte public key (prefix 0-63)."""
    n = 0
    for c in addr:
        n = n * 58 + _B58.index(c)
    leading = len(addr) - len(addr.lstrip("1"))
    raw = b"\x00" * leading + n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    return raw[1:33]  # skip 1-byte prefix, skip 2-byte checksum

def _dot_balance(addr: str) -> float | None:
    """Balance via Polkadot public RPC — no API key required."""
    try:
        import hashlib
        pubkey = _ss58_pubkey(addr)
        # System.Account storage key = twox128("System") + twox128("Account") + blake2_128_concat(pubkey)
        TW = "26aa394eea5630e07c48ae0c9558cef7b99d880ec681799c0cf30e8886371da9"
        b2  = hashlib.blake2b(pubkey, digest_size=16).digest().hex()
        key = "0x" + TW + b2 + pubkey.hex()
        r   = requests.post(
            "https://rpc.polkadot.io",
            json={"jsonrpc": "2.0", "id": 1, "method": "state_getStorage", "params": [key]},
            headers=_JSON_HDR, timeout=8,
        )
        result = r.json().get("result")
        if not result:
            return 0.0  # account never activated or cleaned up
        raw = bytes.fromhex(result[2:])
        # AccountInfo SCALE layout: nonce(4)+consumers(4)+providers(4)+sufficients(4)+free(16)+…
        return int.from_bytes(raw[16:32], "little") / 1e10  # 1 DOT = 10^10 Planck
    except Exception:
        return None

def _get_balance(addr: str, chain: str) -> float | None:
    if chain == "btc":  return _btc_balance(addr)
    if chain == "xpub": return _btc_xpub_balance(addr)
    if chain == "eth":  return _eth_balance(addr)
    if chain == "sol":  return _sol_balance(addr)
    if chain == "dot":  return _dot_balance(addr)
    return None

def _detect_chain(addr: str) -> str | None:
    a = addr.strip()
    if a.startswith("xpub"):                              return "xpub"
    if a.lower().startswith("0x") and len(a) == 42:       return "eth"
    if a.startswith("bc1") and len(a) <= 74:              return "btc"
    if a.startswith(("1", "3")) and len(a) <= 34:         return "btc"
    if 43 <= len(a) <= 44:                                return "sol"
    if a.startswith("1") and 46 <= len(a) <= 50:          return "dot"
    return None


# ── Rendu wallet ──────────────────────────────────────────────────────────────

def _wallet_line(label: str, address: str, chain: str, price_cache: dict) -> str:
    short  = address[:8] + "…" + address[-4:]
    sym    = _CHAIN_SYM.get(chain, "?")
    cid    = _CHAIN_COIN.get(chain)
    p      = price_cache.get(cid, {}) if cid else {}
    bal    = _get_balance(address, chain)
    ticker = "BTC" if chain in ("btc", "xpub") else chain.upper()

    decimals = 6 if chain in ("btc", "xpub") else 4
    bal_s = f"{bal:.{decimals}f} {ticker}" if bal is not None else "⚠ indisponible"

    if bal is not None and p.get("usd"):
        return f"  {sym}  {label} ({short}) — {bal_s} ≈ {_fmt(bal * p['usd'])}"
    return f"  {sym}  {label} ({short}) — {bal_s}"


# ── Sous-commandes ────────────────────────────────────────────────────────────

def _cmd_price(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto price <coin>  (ex: btc, eth, sol)")
    coin = args[0].lower()
    cid  = _cg_id(coin)
    print(f"📡 Prix {coin.upper()}…")
    d = _price_one(cid)
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
        c.execute("INSERT INTO crypto_wallets (label,address,chain) VALUES (?,?,?)", (label, address, chain))
        c.commit()
    except sqlite3.IntegrityError:
        c.close(); return Result.error(f"❌ Label « {label} » déjà utilisé.")
    c.close()
    sym = _CHAIN_SYM.get(chain, chain.upper())
    return Result.success(f"{sym}  Wallet « {label} » ({chain.upper()}) ajouté.")


def _cmd_wallet_list() -> Result:
    c = _conn()
    rows = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucun wallet — /crypto wallet add <adresse> <label>")
    print("🔍 Balances…")
    needed = list({_CHAIN_COIN[ch] for _, _, ch in rows if ch in _CHAIN_COIN})
    cache  = _prices(needed)
    lines  = [f"💼 Portfolio ({len(rows)}) :"]
    lines += [_wallet_line(l, a, ch, cache) for l, a, ch in rows]
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

    seen: dict[str, tuple[str, str]] = {}   # address → (label, chain)
    skipped_tickers: set[str] = set()

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr   = row["Account xpub"].strip()
            name   = row["Account Name"].strip()
            ticker = row["Currency Ticker"].strip().upper()
            if addr in seen:
                continue
            chain = _TICKER_CHAIN.get(ticker)
            if chain is None:
                skipped_tickers.add(ticker)
                continue
            # BTC: only add if it's actually an xpub (not a raw address)
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
            sym = _CHAIN_SYM.get(chain, chain.upper())
            added.append(f"  ✓ {sym}  {label} ({chain.upper()})")
        except sqlite3.IntegrityError:
            dupes.append(f"  ⚠ {label} — déjà présent")
    c.commit(); c.close()

    lines = [f"📥 Import Ledger : {len(added)} ajouté(s), {len(dupes)} ignoré(s)"]
    lines += added + dupes
    if skipped_tickers:
        lines.append(f"  ℹ tickers ignorés (non supportés) : {', '.join(sorted(skipped_tickers))}")
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
    cid = _cg_id(coin)
    c   = _conn()
    c.execute("INSERT INTO crypto_alerts (coin,direction,price) VALUES (?,?,?)", (cid, direction, price))
    c.commit()
    aid   = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    dir_s = "au-dessus de" if direction == "above" else "en-dessous de"
    return Result.success(f"🔔 Alerte #{aid} : {coin.upper()} {dir_s} {_fmt(price)}")


def _cmd_alert_list() -> Result:
    c    = _conn()
    rows = c.execute("SELECT id,coin,direction,price,active FROM crypto_alerts ORDER BY id").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucune alerte — /crypto alert add <coin> <above|below> <prix>")
    lines = ["🔔 Alertes prix :"]
    for aid, coin, direction, price, active in rows:
        status = "✅" if active else "⛔"
        lines.append(f"  {status} #{aid}  {coin.upper()} {'>' if direction=='above' else '<'} {_fmt(price)}")
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
    coin_ids = list({r[1] for r in rows})
    live     = _prices(coin_ids)
    triggered, waiting = [], []
    c = _conn()
    for aid, coin, direction, target in rows:
        cur_price = (live.get(coin) or {}).get("usd")
        if cur_price is None:
            waiting.append(f"  ⚠  #{aid} {coin.upper()} — prix indisponible")
            continue
        hit = (direction == "above" and cur_price >= target) or \
              (direction == "below" and cur_price <= target)
        op  = ">" if direction == "above" else "<"
        line = f"  #{aid}  {coin.upper()} {_fmt(cur_price)} {op} {_fmt(target)}"
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
        needed = list({_CHAIN_COIN[ch] for _, _, ch in wallets if ch in _CHAIN_COIN})
        cache  = _prices(needed)
        lines += ["", f"💼 Wallets ({len(wallets)}) :"]
        lines += [_wallet_line(l, a, ch, cache) for l, a, ch in wallets]
    else:
        lines.append("  Aucun wallet — /crypto wallet add <adresse> <label>")

    print("📡 Prix…")
    top_ids = ["bitcoin", "ethereum", "solana", "polkadot"]
    mkt     = _prices(top_ids)
    lines  += ["", "💹 Marché :"]
    for sym, cid in [("BTC","bitcoin"),("ETH","ethereum"),("SOL","solana"),("DOT","polkadot")]:
        d = mkt.get(cid)
        if d:
            chg = d.get("usd_24h_change") or 0
            lines.append(f"  {sym:<4} {_fmt(d['usd'])}  {'▲' if chg>=0 else '▼'} {chg:+.2f}%")

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
