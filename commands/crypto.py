import sqlite3
import requests
from context import get_conn
from result import Result

_CG = "https://api.coingecko.com/api/v3"
_HDR = {"Accept": "application/json", "User-Agent": "SparkBot/1.0"}

_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
    "xrp": "ripple", "ada": "cardano", "doge": "dogecoin", "dot": "polkadot",
    "avax": "avalanche-2", "matic": "matic-network", "link": "chainlink",
    "ltc": "litecoin", "uni": "uniswap", "atom": "cosmos", "near": "near",
    "trx": "tron", "shib": "shiba-inu", "pepe": "pepe", "op": "optimism",
    "arb": "arbitrum", "sui": "sui", "apt": "aptos",
}

def _cg_id(coin: str) -> str:
    return _IDS.get(coin.lower(), coin.lower())

def _fmt(usd: float) -> str:
    if usd >= 1:      return f"${usd:,.2f}"
    if usd >= 0.0001: return f"${usd:.6f}"
    return f"${usd:.2e}"


# ── DB ────────────────────────────────────────────────────────────────────────

def _conn():
    c = get_conn()
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        chain TEXT NOT NULL CHECK(chain IN ('btc','eth')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS crypto_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT NOT NULL,
        direction TEXT NOT NULL CHECK(direction IN ('above','below')),
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1)""")
    c.commit()
    return c


# ── API ───────────────────────────────────────────────────────────────────────

def _prices(coin_ids: list[str]) -> dict[str, dict]:
    """Retourne {coin_id: {usd, usd_24h_change, usd_market_cap}} en un seul appel."""
    try:
        r = requests.get(f"{_CG}/simple/price", headers=_HDR, timeout=8, params={
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
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

def _eth_balance(addr: str) -> float | None:
    try:
        r = requests.get("https://api.etherscan.io/api", timeout=8, params={
            "module": "account", "action": "balance",
            "address": addr, "tag": "latest", "apikey": "YourApiKeyToken",
        })
        d = r.json()
        return int(d["result"]) / 1e18 if d.get("status") == "1" else None
    except Exception:
        return None

def _detect_chain(addr: str) -> str | None:
    if addr.startswith(("1", "3", "bc1")):
        return "btc"
    if addr.lower().startswith("0x") and len(addr) == 42:
        return "eth"
    return None


# ── Rendu wallet ──────────────────────────────────────────────────────────────

def _wallet_line(label: str, address: str, chain: str, price_cache: dict) -> str:
    short = address[:8] + "…" + address[-4:]
    if chain == "btc":
        bal = _btc_balance(address)
        p = price_cache.get("bitcoin", {})
        if bal is not None and p:
            return f"  ₿  {label} ({short}) — {bal:.6f} BTC ≈ {_fmt(bal * p['usd'])}"
        return f"  ₿  {label} ({short}) — {f'{bal:.6f} BTC' if bal is not None else '⚠️ indisponible'}"
    else:
        bal = _eth_balance(address)
        p = price_cache.get("ethereum", {})
        if bal is not None and p:
            return f"  Ξ  {label} ({short}) — {bal:.4f} ETH ≈ {_fmt(bal * p['usd'])}"
        return f"  Ξ  {label} ({short}) — {f'{bal:.4f} ETH' if bal is not None else '⚠️ indisponible'}"


# ── Sous-commandes ────────────────────────────────────────────────────────────

def _cmd_price(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto price <coin>  (ex: btc, eth, sol)")
    coin = args[0].lower()
    cid = _cg_id(coin)
    print(f"📡 Prix {coin.upper()}…")
    d = _price_one(cid)
    if not d:
        return Result.error(f"❌ Coin « {coin} » introuvable.")
    chg = d.get("usd_24h_change") or 0
    mc  = d.get("usd_market_cap") or 0
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
            g = requests.get(f"{_CG}/global", headers=_HDR, timeout=5).json().get("data", {})
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
        return Result.error("❌ Adresse non reconnue (BTC: 1/3/bc1…, ETH: 0x…42 chars).")
    c = _conn()
    try:
        c.execute("INSERT INTO crypto_wallets (label,address,chain) VALUES (?,?,?)", (label, address, chain))
        c.commit()
    except sqlite3.IntegrityError:
        c.close(); return Result.error(f"❌ Label « {label} » déjà utilisé.")
    c.close()
    return Result.success(f"{'₿' if chain=='btc' else 'Ξ'}  Wallet « {label} » ({chain.upper()}) ajouté.")


def _cmd_wallet_list() -> Result:
    c = _conn()
    rows = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucun wallet — /crypto wallet add <adresse> <label>")
    print("🔍 Balances…")
    needed = list({("bitcoin" if r[2]=="btc" else "ethereum") for r in rows})
    cache  = _prices(needed)
    lines  = [f"💼 Portfolio ({len(rows)}) :"]
    lines += [_wallet_line(l, a, ch, cache) for l, a, ch in rows]
    return Result.success("\n".join(lines))


def _cmd_wallet_remove(args: list) -> Result:
    if not args:
        return Result.error("Usage : /crypto wallet remove <label>")
    label = " ".join(args)
    c = _conn()
    cur = c.execute("DELETE FROM crypto_wallets WHERE label=?", (label,))
    c.commit(); c.close()
    return Result.success(f"🗑️  Wallet « {label} » supprimé.") if cur.rowcount \
        else Result.error(f"❌ Wallet « {label} » introuvable.")


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
    c = _conn()
    c.execute("INSERT INTO crypto_alerts (coin,direction,price) VALUES (?,?,?)", (cid, direction, price))
    c.commit()
    aid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    dir_s = "au-dessus de" if direction == "above" else "en-dessous de"
    return Result.success(f"🔔 Alerte #{aid} : {coin.upper()} {dir_s} {_fmt(price)}")


def _cmd_alert_list() -> Result:
    c = _conn()
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
    c = _conn()
    cur = c.execute("DELETE FROM crypto_alerts WHERE id=?", (aid,))
    c.commit(); c.close()
    return Result.success(f"🗑️  Alerte #{aid} supprimée.") if cur.rowcount \
        else Result.error(f"❌ Alerte #{aid} introuvable.")


def _cmd_alert_check() -> Result:
    c = _conn()
    rows = c.execute("SELECT id,coin,direction,price FROM crypto_alerts WHERE active=1").fetchall()
    c.close()
    if not rows:
        return Result.success("Aucune alerte active.")
    print("📡 Vérification des alertes…")
    coin_ids = list({r[1] for r in rows})
    live = _prices(coin_ids)
    triggered, waiting = [], []
    c = _conn()
    for aid, coin, direction, target in rows:
        cur_price = (live.get(coin) or {}).get("usd")
        if cur_price is None:
            waiting.append(f"  ⚠️  #{aid} {coin.upper()} — prix indisponible")
            continue
        hit = (direction == "above" and cur_price >= target) or \
              (direction == "below" and cur_price <= target)
        op = ">" if direction == "above" else "<"
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
    c = _conn()
    wallets = c.execute("SELECT label,address,chain FROM crypto_wallets ORDER BY id").fetchall()
    n_alerts = c.execute("SELECT COUNT(*) FROM crypto_alerts WHERE active=1").fetchone()[0]
    c.close()

    lines = ["📊 Résumé crypto :"]

    if wallets:
        print("🔍 Balances…")
        needed = list({("bitcoin" if ch=="btc" else "ethereum") for _,_,ch in wallets})
        cache  = _prices(needed)
        lines += ["", f"💼 Wallets ({len(wallets)}) :"]
        lines += [_wallet_line(l, a, ch, cache) for l, a, ch in wallets]
    else:
        lines.append("  Aucun wallet — /crypto wallet add <adresse> <label>")

    print("📡 Prix…")
    top_ids = ["bitcoin", "ethereum", "solana"]
    mkt = _prices(top_ids)
    lines.append("")
    lines.append("💹 Marché :")
    for sym, cid in [("BTC","bitcoin"),("ETH","ethereum"),("SOL","solana")]:
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

    if sub == "price":
        return _cmd_price(parts[1:])

    if sub == "news":
        return _cmd_news()

    if sub == "wallet":
        action = parts[1].lower() if len(parts) > 1 else ""
        if action == "add":    return _cmd_wallet_add(parts[2:])
        if action == "list":   return _cmd_wallet_list()
        if action == "remove": return _cmd_wallet_remove(parts[2:])
        return Result.error(
            "Sous-commandes wallet : add <adresse> <label> | list | remove <label>")

    if sub == "alert":
        action = parts[1].lower() if len(parts) > 1 else ""
        if action == "add":    return _cmd_alert_add(parts[2:])
        if action == "list":   return _cmd_alert_list()
        if action == "remove": return _cmd_alert_remove(parts[2:])
        if action == "check":  return _cmd_alert_check()
        return Result.error(
            "Sous-commandes alert : add <coin> <above|below> <prix> | list | remove <id> | check")

    return Result.error(f"Sous-commande « {sub} » inconnue. Tape /help crypto.")
