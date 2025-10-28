import click
from utils.coingecko_client import CoinGeckoClient

import os

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

client = CoinGeckoClient()

@click.group(help="💰 CoinGecko CLI 工具 —— 查询币价、市场与历史数据")
def cli():
    pass

@cli.command()
@click.argument("ids")
@click.option("--vs", default="usd", help="对比货币")
def price(ids, vs):
    """获取币种当前价格。例子: cg.py price bitcoin,ethereum"""
    data = client.get_price(ids, vs)
    click.secho("\n💰 当前价格：", fg="cyan", bold=True)
    for coin, info in data.items():
        click.secho(f"{coin.capitalize():<12}: {info[vs]} {vs.upper()}", fg="green")

@cli.command()
@click.option("--top", default=10, help="获取市值前 N 名币种")
@click.option("--vs", default="usd", help="对比货币")
def market(top, vs):
    """获取市值前 N 名的币种市场数据"""
    data = client.get_market(vs_currency=vs, per_page=top)
    click.secho(f"\n📈 市场前 {top}：\n", fg="cyan", bold=True)

    for coin in data:
        name = coin["name"]
        price_val = coin["current_price"]
        change = coin.get("price_change_percentage_24h", 0.0)
        color = "green" if change >= 0 else "red"
        sign = "+" if change >= 0 else ""
        click.secho(f"{name:<12} {price_val:>12.2f} {vs.upper():<5} ({sign}{change:.2f}%)", fg=color)

@cli.command()
@click.argument("coin")
@click.argument("date")
def history(coin, date):
    """获取币种在指定日期的历史价格。例子: cg.py history bitcoin 01-01-2025"""
    data = client.get_history(coin, date)
    if data and "market_data" in data:
        price_val = data["market_data"]["current_price"]["usd"]
        click.secho(f"{coin.capitalize()} 在 {date} 的价格是 {price_val} USD 💾", fg="magenta")

if __name__ == "__main__":
    cli()
