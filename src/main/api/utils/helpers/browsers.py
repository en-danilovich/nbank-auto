def norm_browser_name(value: str) -> str:
    s = str(value).strip().lower()
    return {"chrome": "chromium", "ff": "firefox"}.get(s, s)