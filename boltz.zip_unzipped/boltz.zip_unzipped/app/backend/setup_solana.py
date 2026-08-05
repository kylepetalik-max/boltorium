"""
Solana Setup Script — Generate keypair, airdrop SOL, create RMR SPL token on devnet.
Run once to bootstrap. Saves results to /app/backend/.env and solana_keypair.json.
"""
import asyncio
import json
import base58
from pathlib import Path

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import create_account, CreateAccountParams
from spl.token.constants import TOKEN_PROGRAM_ID, MINT_LEN
from spl.token.instructions import (
    initialize_mint, InitializeMintParams,
    create_associated_token_account,
    get_associated_token_address,
    mint_to, MintToParams,
)

RPC_URL = "https://api.devnet.solana.com"
DECIMALS = 6
INITIAL_SUPPLY = 10_000_000  # 10M RMR

def build_and_send(client, payer, instructions, extra_signers=None):
    """Build a VersionedTransaction, sign, and send."""
    signers = [payer] + (extra_signers or [])
    bh = client.get_latest_blockhash(Confirmed).value.blockhash
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=instructions,
        address_lookup_table_accounts=[],
        recent_blockhash=bh,
    )
    tx = VersionedTransaction(msg, signers)
    result = client.send_transaction(tx)
    client.confirm_transaction(result.value, Confirmed)
    return result.value

def main():
    client = Client(RPC_URL)

    # 1. Generate mint authority keypair
    payer = Keypair()
    print(f"Mint Authority: {payer.pubkey()}")
    secret_b58 = base58.b58encode(bytes(payer)).decode()

    # 2. Airdrop 2 SOL
    print("Airdropping 2 SOL...")
    sig = client.request_airdrop(payer.pubkey(), 2_000_000_000, Confirmed)
    client.confirm_transaction(sig.value, Confirmed)
    bal = client.get_balance(payer.pubkey(), Confirmed)
    print(f"Balance: {bal.value / 1e9:.2f} SOL")

    # 3. Create RMR token mint
    mint_kp = Keypair()
    print(f"RMR Mint: {mint_kp.pubkey()}")

    rent = client.get_minimum_balance_for_rent_exemption(MINT_LEN, Confirmed)

    tx_sig = build_and_send(client, payer, [
        create_account(CreateAccountParams(
            from_pubkey=payer.pubkey(),
            to_pubkey=mint_kp.pubkey(),
            lamports=rent.value,
            space=MINT_LEN,
            owner=TOKEN_PROGRAM_ID,
        )),
        initialize_mint(InitializeMintParams(
            decimals=DECIMALS,
            mint_authority=payer.pubkey(),
            freeze_authority=payer.pubkey(),
            program_id=TOKEN_PROGRAM_ID,
            mint=mint_kp.pubkey(),
        )),
    ], extra_signers=[mint_kp])
    print(f"Mint created! TX: {tx_sig}")

    # 4. Create ATA for treasury
    treasury_ata = get_associated_token_address(payer.pubkey(), mint_kp.pubkey())
    ix_ata = create_associated_token_account(payer.pubkey(), payer.pubkey(), mint_kp.pubkey())
    tx_sig2 = build_and_send(client, payer, [ix_ata])
    print(f"Treasury ATA: {treasury_ata} TX: {tx_sig2}")

    # 5. Mint initial supply
    raw_amount = INITIAL_SUPPLY * (10 ** DECIMALS)
    ix_mint = mint_to(MintToParams(
        program_id=TOKEN_PROGRAM_ID,
        mint=mint_kp.pubkey(),
        dest=treasury_ata,
        mint_authority=payer.pubkey(),
        amount=raw_amount,
        signers=[],
    ))
    tx_sig3 = build_and_send(client, payer, [ix_mint])
    print(f"Minted {INITIAL_SUPPLY:,} RMR! TX: {tx_sig3}")

    # 6. Save keypairs
    keypair_data = {
        "payer_secret_b58": secret_b58,
        "payer_pubkey": str(payer.pubkey()),
        "mint_pubkey": str(mint_kp.pubkey()),
        "mint_secret_b58": base58.b58encode(bytes(mint_kp)).decode(),
        "treasury_ata": str(treasury_ata),
        "decimals": DECIMALS,
        "initial_supply": INITIAL_SUPPLY,
        "network": "devnet",
    }
    kp_path = Path(__file__).parent / "solana_keypair.json"
    kp_path.write_text(json.dumps(keypair_data, indent=2))
    print(f"Keypairs saved to {kp_path}")

    # 7. Update .env
    env_path = Path(__file__).parent / ".env"
    env_text = env_path.read_text()
    new_vars = {
        "SOLANA_PRIVATE_KEY": secret_b58,
        "RMR_MINT_ADDRESS": str(mint_kp.pubkey()),
        "SOLANA_RPC_URL": RPC_URL,
        "RMR_TREASURY_ATA": str(treasury_ata),
        "RMR_DECIMALS": str(DECIMALS),
    }
    for k, v in new_vars.items():
        lines = env_text.split("\n")
        lines = [l for l in lines if not l.startswith(f"{k}=")]
        env_text = "\n".join(lines)
        env_text = env_text.rstrip("\n") + f"\n{k}={v}\n"
    env_path.write_text(env_text)

    print(f"\n=== RMR Token Live on Devnet ===")
    print(f"  Mint:     {mint_kp.pubkey()}")
    print(f"  Treasury: {treasury_ata}")
    print(f"  Supply:   {INITIAL_SUPPLY:,} RMR")
    print(f"  Explorer: https://explorer.solana.com/address/{mint_kp.pubkey()}?cluster=devnet")

    client.close()

if __name__ == "__main__":
    main()
