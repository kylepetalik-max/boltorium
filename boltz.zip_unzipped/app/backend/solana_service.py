"""
Solana Service Module — Handles all on-chain RMR token operations.
Feature-flagged: works in demo mode if Solana libs or config are missing.
"""
import os
import logging
import base58
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("solana_service")

# Lazy imports — only loaded when actually called
_solana_loaded = False
_Client = None
_Keypair = None
_Pubkey = None
_VersionedTransaction = None
_MessageV0 = None
_TOKEN_PROGRAM_ID = None
_MINT_LEN = None

def _load_solana():
    """Lazy-load Solana libraries. Returns True if successful."""
    global _solana_loaded, _Client, _Keypair, _Pubkey
    global _VersionedTransaction, _MessageV0, _TOKEN_PROGRAM_ID, _MINT_LEN
    if _solana_loaded:
        return True
    try:
        from solana.rpc.api import Client
        from solana.rpc.commitment import Confirmed
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.transaction import VersionedTransaction
        from solders.message import MessageV0
        from spl.token.constants import TOKEN_PROGRAM_ID, MINT_LEN
        _Client = Client
        _Keypair = Keypair
        _Pubkey = Pubkey
        _VersionedTransaction = VersionedTransaction
        _MessageV0 = MessageV0
        _TOKEN_PROGRAM_ID = TOKEN_PROGRAM_ID
        _MINT_LEN = MINT_LEN
        _solana_loaded = True
        return True
    except ImportError as e:
        logger.warning(f"Solana libraries not available: {e}")
        return False


# Config from env
SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PRIVATE_KEY = os.environ.get("SOLANA_PRIVATE_KEY")
RMR_MINT_ADDRESS = os.environ.get("RMR_MINT_ADDRESS")
RMR_TREASURY_ATA = os.environ.get("RMR_TREASURY_ATA")
RMR_DECIMALS = int(os.environ.get("RMR_DECIMALS", "6"))


def is_real_mode():
    """Check if real on-chain mode is available."""
    return bool(SOLANA_PRIVATE_KEY and RMR_MINT_ADDRESS and _load_solana())


def get_status():
    """Get Solana connection status."""
    if not _load_solana():
        return {
            "connected": False,
            "mode": "demo",
            "cluster": "devnet",
            "rpc_url": SOLANA_RPC_URL,
            "minting_enabled": False,
            "mint_address": RMR_MINT_ADDRESS,
            "note": "Solana libraries not loaded — demo mode active"
        }

    try:
        client = _Client(SOLANA_RPC_URL)
        version = client.get_version()
        real = is_real_mode()
        return {
            "connected": True,
            "mode": "live" if real else "demo",
            "cluster": "devnet" if "devnet" in SOLANA_RPC_URL else "mainnet-beta",
            "rpc_url": SOLANA_RPC_URL,
            "minting_enabled": real,
            "mint_address": RMR_MINT_ADDRESS,
            "treasury": RMR_TREASURY_ATA,
            "decimals": RMR_DECIMALS,
            "version": str(version.value.solana_core) if version.value else "unknown",
        }
    except Exception as e:
        return {
            "connected": False,
            "mode": "demo",
            "error": str(e),
            "minting_enabled": False,
            "mint_address": RMR_MINT_ADDRESS,
        }


def get_balance(wallet_address: str) -> dict:
    """Get on-chain RMR token balance for a wallet."""
    if not _load_solana() or not RMR_MINT_ADDRESS:
        return {"balance": 0, "mode": "demo", "wallet": wallet_address}

    try:
        from spl.token.instructions import get_associated_token_address
        client = _Client(SOLANA_RPC_URL)
        owner = _Pubkey.from_string(wallet_address)
        mint = _Pubkey.from_string(RMR_MINT_ADDRESS)
        ata = get_associated_token_address(owner, mint)

        resp = client.get_token_account_balance(ata)
        if resp.value:
            return {
                "balance": float(resp.value.ui_amount_string),
                "raw": int(resp.value.amount),
                "decimals": resp.value.decimals,
                "token_account": str(ata),
                "mode": "live",
                "wallet": wallet_address,
            }
        return {"balance": 0, "mode": "live", "wallet": wallet_address, "token_account": str(ata)}
    except Exception as e:
        logger.warning(f"Balance check failed for {wallet_address}: {e}")
        return {"balance": 0, "mode": "demo", "wallet": wallet_address, "error": str(e)}


def mint_tokens(wallet_address: str, amount: float) -> dict:
    """Mint RMR tokens to a user's wallet on-chain."""
    tx_id = f"mint_{uuid.uuid4().hex[:16]}"

    if not is_real_mode():
        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": amount,
            "wallet": wallet_address,
            "mode": "demo",
            "signature": None,
            "note": "Demo mode — configure SOLANA_PRIVATE_KEY and RMR_MINT_ADDRESS for real minting",
        }

    try:
        from solana.rpc.commitment import Confirmed
        from spl.token.instructions import (
            get_associated_token_address,
            create_associated_token_account,
            mint_to, MintToParams,
        )

        client = _Client(SOLANA_RPC_URL)
        payer = _Keypair.from_bytes(base58.b58decode(SOLANA_PRIVATE_KEY))
        mint = _Pubkey.from_string(RMR_MINT_ADDRESS)
        owner = _Pubkey.from_string(wallet_address)
        ata = get_associated_token_address(owner, mint)

        # Check if ATA exists, create if not
        ata_info = client.get_account_info(ata)
        instructions = []
        if ata_info.value is None:
            instructions.append(create_associated_token_account(payer.pubkey(), owner, mint))

        raw_amount = int(amount * (10 ** RMR_DECIMALS))
        instructions.append(mint_to(MintToParams(
            program_id=_TOKEN_PROGRAM_ID,
            mint=mint,
            dest=ata,
            mint_authority=payer.pubkey(),
            amount=raw_amount,
            signers=[],
        )))

        bh = client.get_latest_blockhash(Confirmed).value.blockhash
        msg = _MessageV0.try_compile(
            payer=payer.pubkey(),
            instructions=instructions,
            address_lookup_table_accounts=[],
            recent_blockhash=bh,
        )
        tx = _VersionedTransaction(msg, [payer])
        result = client.send_transaction(tx)
        client.confirm_transaction(result.value, Confirmed)

        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": amount,
            "wallet": wallet_address,
            "mode": "live",
            "signature": str(result.value),
            "explorer": f"https://explorer.solana.com/tx/{result.value}?cluster=devnet",
        }
    except Exception as e:
        logger.error(f"Mint failed: {e}")
        return {"success": False, "error": str(e), "transaction_id": tx_id, "mode": "live"}


def transfer_tokens(from_secret_b58: str, to_wallet: str, amount: float) -> dict:
    """Transfer RMR tokens between wallets on-chain."""
    tx_id = f"transfer_{uuid.uuid4().hex[:16]}"

    if not _load_solana() or not RMR_MINT_ADDRESS:
        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": amount,
            "to": to_wallet,
            "mode": "demo",
            "signature": None,
        }

    try:
        from solana.rpc.commitment import Confirmed
        from spl.token.instructions import (
            get_associated_token_address,
            create_associated_token_account,
            transfer_checked, TransferCheckedParams,
        )

        client = _Client(SOLANA_RPC_URL)
        sender = _Keypair.from_bytes(base58.b58decode(from_secret_b58))
        mint = _Pubkey.from_string(RMR_MINT_ADDRESS)
        recipient = _Pubkey.from_string(to_wallet)

        source_ata = get_associated_token_address(sender.pubkey(), mint)
        dest_ata = get_associated_token_address(recipient, mint)

        # Ensure recipient ATA exists (payer creates it using mint authority for fee)
        payer = _Keypair.from_bytes(base58.b58decode(SOLANA_PRIVATE_KEY))
        instructions = []
        dest_info = client.get_account_info(dest_ata)
        if dest_info.value is None:
            instructions.append(create_associated_token_account(payer.pubkey(), recipient, mint))

        raw_amount = int(amount * (10 ** RMR_DECIMALS))
        instructions.append(transfer_checked(TransferCheckedParams(
            program_id=_TOKEN_PROGRAM_ID,
            source=source_ata,
            mint=mint,
            dest=dest_ata,
            owner=sender.pubkey(),
            amount=raw_amount,
            decimals=RMR_DECIMALS,
            signers=[],
        )))

        bh = client.get_latest_blockhash(Confirmed).value.blockhash
        signers = [payer, sender] if payer.pubkey() != sender.pubkey() else [sender]
        msg = _MessageV0.try_compile(
            payer=payer.pubkey(),
            instructions=instructions,
            address_lookup_table_accounts=[],
            recent_blockhash=bh,
        )
        tx = _VersionedTransaction(msg, signers)
        result = client.send_transaction(tx)
        client.confirm_transaction(result.value, Confirmed)

        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": amount,
            "from": str(sender.pubkey()),
            "to": to_wallet,
            "mode": "live",
            "signature": str(result.value),
            "explorer": f"https://explorer.solana.com/tx/{result.value}?cluster=devnet",
        }
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        return {"success": False, "error": str(e), "transaction_id": tx_id, "mode": "live"}
