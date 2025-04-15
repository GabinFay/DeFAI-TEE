"""
Formatting utilities for Flare Bot.
"""

def format_tx_hash_as_link(tx_hash, html=False):
    """
    Format a transaction hash as a clickable link to the Flare Explorer
    
    Args:
        tx_hash: The transaction hash
        html: Whether to return HTML format (for UI elements) or Markdown format (for chat messages)
        
    Returns:
        str: Formatted link
    """
    explorer_url = f"https://flare-explorer.flare.network/tx/{tx_hash}"
    if html:
        return f"<a href='{explorer_url}' target='_blank'>View on Flare Explorer</a>"
    else:
        return f"[View on Flare Explorer]({explorer_url})" 