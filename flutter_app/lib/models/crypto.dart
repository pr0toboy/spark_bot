class CryptoMarketItem {
  final String symbol;
  final double priceUsd;
  final double change24h;

  CryptoMarketItem.fromJson(Map<String, dynamic> j)
      : symbol = j['symbol'] as String,
        priceUsd = (j['price_usd'] as num).toDouble(),
        change24h = (j['change_24h'] as num).toDouble();
}

class CryptoWallet {
  final String label;
  final String address;
  final String chain;
  final double? balance;
  final double? balanceUsd;

  CryptoWallet.fromJson(Map<String, dynamic> j)
      : label = j['label'] as String,
        address = j['address'] as String,
        chain = j['chain'] as String,
        balance = (j['balance'] as num?)?.toDouble(),
        balanceUsd = (j['balance_usd'] as num?)?.toDouble();
}

class CryptoPortfolio {
  final List<CryptoWallet> wallets;
  final List<CryptoMarketItem> market;
  final double? totalUsd;

  CryptoPortfolio.fromJson(Map<String, dynamic> j)
      : wallets = (j['wallets'] as List)
            .map((e) => CryptoWallet.fromJson(e as Map<String, dynamic>))
            .toList(),
        market = (j['market'] as List)
            .map((e) => CryptoMarketItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalUsd = (j['total_usd'] as num?)?.toDouble();
}

class CryptoAlert {
  final int id;
  final String coin;
  final String direction;
  final double price;
  final bool active;

  CryptoAlert.fromJson(Map<String, dynamic> j)
      : id = j['id'] as int,
        coin = j['coin'] as String,
        direction = j['direction'] as String,
        price = (j['price'] as num).toDouble(),
        active = j['active'] as bool;
}

class CryptoTrend {
  final int? rank;
  final String symbol;
  final String name;

  CryptoTrend.fromJson(Map<String, dynamic> j)
      : rank = j['rank'] as int?,
        symbol = j['symbol'] as String,
        name = j['name'] as String;
}
