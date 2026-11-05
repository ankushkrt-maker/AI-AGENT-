from fastapi import APIRouter, HTTPException
from app.futures.scanner import scan_all_futures
from app.alerts.telegram import send_telegram

router = APIRouter()
_sent = {}

@router.get("/futures/scan")
async def futures_scan(notify: bool = True):
    try:
        data = await scan_all_futures()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Binance Futures scan failed: {str(exc)[:200]}")
    if notify:
        for row in data.get("results", []):
            decision = row.get("decision")
            if decision not in ("LONG", "SHORT"):
                continue
            key = (row.get("symbol"), decision)
            if key in _sent:
                continue
            reasons = row.get("reasons", [])
            msg = (
                f"\U0001f4a1 LIQUIDITY HUNTER | {decision}\n"
                f"Pair: {row.get('symbol')}\n"
                f"Price: {row.get('price')}\n"
                f"Score: {row.get('confidence')}/100\n"
                f"5m RVOL: {row.get('rvol')}x | OI change: {row.get('oi_change_pct')}%\n"
                f"Taker buy ratio: {row.get('taker_buy_ratio')} | Funding: {row.get('funding_pct')}%\n"
                f"Example stop: {row.get('stop')}\n"
                f"Risk budget: INR {row.get('risk_budget_inr')}\n"
                f"Reasons: {', '.join(reasons) if isinstance(reasons, list) else reasons}\n"
                "Research alert only. No auto-trading. Confirm setup manually."
            )
            result = await send_telegram(msg)
            if result.get("sent"):
                _sent[key] = True
    data["telegram_configured"] = bool(__import__("os").getenv("TELEGRAM_BOT_TOKEN") and __import__("os").getenv("TELEGRAM_CHAT_ID"))
    return data

@router.post("/futures/telegram/test")
async def telegram_test():
    result = await send_telegram("Liquidity Hunter AI: Telegram alerts connected. Signal-only mode is active.")
    if not result.get("sent"):
        raise HTTPException(status_code=400, detail=result.get("reason", "Telegram not configured"))
    return {"ok": True, "message": "Test alert sent"}
