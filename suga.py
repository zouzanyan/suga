import click
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils.coingecko_client import client

console = Console()


# import os
#
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"



@click.group(help="💰 Suga CLI - 优雅的终端加密行情工具")
@click.version_option("0.2.0", prog_name="suga")
def cli():
    pass


# ========================================================
# 🧭 实时价格查询
# ========================================================
@cli.command()
@click.argument("ids")
@click.option("--vs", default="usd", show_default=True, help="对比货币（usd, cny 等）")
@click.option("--watch", is_flag=True, help="实时刷新显示价格")
@click.option("--interval", default=5, show_default=True, help="刷新间隔（秒）")
def price(ids, vs, watch, interval):
    """获取币种当前价格。例: suga price bitcoin,ethereum"""
    ids = [x.strip() for x in ids.split(",")]

    def render_table():
        data = client.get_price(ids, vs)
        table = Table(title=f"💰 实时价格 ({vs.upper()})", header_style="bold cyan")
        table.add_column("币种", justify="left", style="bold")
        table.add_column("价格", justify="right")
        for coin, info in data.items():
            val = info.get(vs, "?")
            table.add_row(coin.capitalize(), f"{val:,.2f}")
        return table

    if watch:
        with Live(render_table(), refresh_per_second=1):
            while True:
                time.sleep(interval)
                console.clear()
                console.print(render_table())
    else:
        console.print(render_table())


# ========================================================
# 📊 市场列表
# ========================================================
@cli.command()
@click.option("--top", default=10, show_default=True, help="获取市值前 N 名币种")
@click.option("--vs", default="usd", show_default=True, help="对比货币")
@click.option("--sort", type=click.Choice(["price", "change", "volume", "market_cap"]), default="market_cap", help="排序依据")
@click.option("--refresh", is_flag=True, help="实时刷新模式")
def market(top, vs, sort, refresh):
    """查看市场数据（默认显示市值前 N 名）"""
    def render():
        data = client.get_market(vs_currency=vs, per_page=top)
        table = Table(title=f"📈 市场前 {top} ({vs.upper()})", header_style="bold cyan")
        table.add_column("币种", justify="left", style="bold")
        table.add_column("价格", justify="right")
        table.add_column("24h变化", justify="right")
        table.add_column("市值", justify="right")
        for coin in data:
            name = coin["name"]
            price_val = coin["current_price"]
            change = coin.get("price_change_percentage_24h", 0.0)
            color = "green" if change >= 0 else "red"
            table.add_row(
                name,
                f"{price_val:,.5f}",
                f"[{color}]{change:+.2f}%[/]",
                f"{coin['market_cap']:,}"
            )
        return table

    if refresh:
        with Live(render(), refresh_per_second=1) as live:
            while True:
                time.sleep(5)
                live.update(render())  # 只更新，不用 clear 或 console.print
    else:
        console.print(render())


# ========================================================
# 🕰️ 历史价格查询
# ========================================================
@cli.command()
@click.argument("coin")
@click.argument("date")
@click.option("--vs", default="usd", show_default=True, help="对比货币")
def history(coin, date, vs):
    """查询币种在指定日期的历史价格。例: suga history bitcoin 01-01-2024"""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="正在查询历史数据...", total=None)
        data = client.get_history(coin, date)

    if not data or "market_data" not in data:
        console.print(f"⚠️ 未找到 {coin} 在 {date} 的历史数据。", style="yellow")
        return

    price_val = data["market_data"]["current_price"].get(vs)
    console.print(f"📅 [bold]{coin.capitalize()}[/] 在 {date} 的价格是 [cyan]{price_val} {vs.upper()}[/]")


# ========================================================
# ⚙️ 全局错误处理
# ========================================================
@cli.result_callback()
def process_result(result, **kwargs):
    """统一错误捕获"""
    if isinstance(result, Exception):
        console.print(f"[red]❌ 出错：{result}[/]")


if __name__ == "__main__":
    cli()
