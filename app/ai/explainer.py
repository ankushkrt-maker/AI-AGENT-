import os

def explain(symbol, scores, features):
    top = max(scores, key=scores.get)
    return {"summary": f"{symbol}: strongest engine is {top} with score {scores[top]:.0f}/100.", "disclaimer": "Quantitative heuristic only; not a guarantee or financial advice.", "features": features}

def llm_status():
    return {"configured": bool(os.getenv("GEMINI_API_KEY")), "provider": "Gemini optional"}
