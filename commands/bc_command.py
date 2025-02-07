# BC - returns <ip>
# bc_command.py

from typing import List

async def handle_bc_command(host: str, args: List[str]) -> str:
    """
    Handle BC command - returns bank code (IP address)
    Args:
        host: Server's IP address
        args: Command arguments (should be empty for BC)
    Returns:
        Response string in format "BC <ip>"
    """
    if args:
        return "ER BC command takes no arguments"
    return f"BC {host}"
