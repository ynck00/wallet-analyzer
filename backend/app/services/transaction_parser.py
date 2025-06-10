from dataclasses import dataclass

@dataclass
class Swap:
    signature: str
    timestamp: int
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float

def parse_transaction(tx: dict, wallet_address: str) -> Swap | None:
    """
    Parses a Helius `getParsedTransaction` response to find swap details.
    This is a simplified parser focusing on token balance changes. A robust
    implementation would need to check instruction types for specific DEX programs.
    """
    # Enhanced transaction format detection
    # 1. Direct `events.swap` (preferred – already decoded by Helius)
    swap_event = tx.get("events", {}).get("swap") if isinstance(tx.get("events"), dict) else None
    if swap_event:
        # Find token that left and entered the wallet
        from_token = None
        from_amount = 0.0
        to_token = None
        to_amount = 0.0

        for ti in swap_event.get("tokenInputs", []):
            if ti.get("userAccount") == wallet_address:
                mint = ti.get("mint")
                amt_raw = ti.get("tokenAmount") or 0
                decimals = ti.get("decimals") or 0
                try:
                    amt = float(amt_raw) / (10 ** int(decimals)) if decimals else float(amt_raw)
                except (ValueError, TypeError):
                    amt = 0
                from_token, from_amount = mint, amt
                break

        for to in swap_event.get("tokenOutputs", []):
            if to.get("userAccount") == wallet_address:
                mint = to.get("mint")
                amt_raw = to.get("tokenAmount") or 0
                decimals = to.get("decimals") or 0
                try:
                    amt = float(amt_raw) / (10 ** int(decimals)) if decimals else float(amt_raw)
                except (ValueError, TypeError):
                    amt = 0
                to_token, to_amount = mint, amt
                break

        if from_token and to_token and from_token != to_token and from_amount > 0 and to_amount > 0:
            return Swap(
                signature=tx.get("signature") or tx.get("transactionSignature") or "",
                timestamp=tx.get("timestamp") or tx.get("blockTime", 0),
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=to_amount,
            )

    if "tokenTransfers" in tx and "signature" in tx:
        decreased_mints = []
        increased_mints = []

        for t in tx.get("tokenTransfers", []):
            mint = t.get("mint")
            amount_raw = t.get("tokenAmount", 0)
            decimals = t.get("decimals") or 0
            try:
                amount = float(amount_raw) / (10 ** int(decimals)) if decimals else float(amount_raw)
            except (ValueError, TypeError):
                amount = 0
            if t.get("fromUserAccount") == wallet_address:
                decreased_mints.append((mint, amount))
            if t.get("toUserAccount") == wallet_address:
                increased_mints.append((mint, amount))

        # If exactly one decrease and one increase treat as swap
        if len(decreased_mints) == 1 and len(increased_mints) == 1:
            from_token, from_amount = decreased_mints[0]
            to_token, to_amount = increased_mints[0]
            return Swap(
                signature=tx["signature"],
                timestamp=tx.get("timestamp") or tx.get("blockTime", 0),
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=to_amount,
            )

    # Original parsedTransaction format
    meta = tx.get("meta")
    if tx and meta is not None and not meta.get("err"):
        pre_balances = {item['mint']: item for item in meta.get("preTokenBalances", []) if item.get('owner') == wallet_address}
        post_balances = {item['mint']: item for item in meta.get("postTokenBalances", []) if item.get('owner') == wallet_address}

        all_mints = set(pre_balances.keys()) | set(post_balances.keys())
        decreased_mints = []
        increased_mints = []

        for mint in all_mints:
            pre_ui_amount = pre_balances.get(mint, {}).get("uiTokenAmount", {}).get("uiAmount", 0)
            post_ui_amount = post_balances.get(mint, {}).get("uiTokenAmount", {}).get("uiAmount", 0)

            if post_ui_amount < pre_ui_amount:
                decreased_mints.append((mint, pre_ui_amount - post_ui_amount))
            elif post_ui_amount > pre_ui_amount:
                increased_mints.append((mint, post_ui_amount - pre_ui_amount))

        if len(decreased_mints) == 1 and len(increased_mints) == 1:
            from_token, from_amount = decreased_mints[0]
            to_token, to_amount = increased_mints[0]
            return Swap(
                signature=tx["transaction"]["signatures"][0],
                timestamp=tx.get("blockTime", 0),
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=to_amount,
            )

    return None 