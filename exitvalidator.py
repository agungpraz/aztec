import requests
from web3 import Web3
import json

# Configuration
RPC_URL = "https://your-aztec-network-rpc-endpoint"  # Replace with Aztec Network's Ethereum RPC endpoint
PRIVATE_KEY = "your_private_key"  # Replace with your Ethereum account private key
CONTRACT_ADDRESS = "0xYourValidatorRegistryContractAddress"  # Replace with actual contract address
AZTEC_SCAN_API = "https://aztecscan.xyz/api/validators"  # Hypothetical API endpoint

# Hypothetical ABI for the validator registry contract (simplified)
CONTRACT_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "validator", "type": "address"}],
        "name": "finalizeExit",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getValidators",
        "outputs": [
            {"name": "validators", "type": "address[]"},
            {"name": "statuses", "type": "uint256[]"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Check connection
if not w3.is_connected():
    raise Exception("Failed to connect to RPC endpoint")

# Set up account
account = w3.eth.account.from_key(PRIVATE_KEY)

# Initialize contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def get_exiting_validators():
    """
    Fetch validators with status 3 (EXITING) from AztecScan API or contract.
    Returns a list of validator addresses.
    """
    try:
        # Option 1: Fetch from AztecScan API (hypothetical)
        response = requests.get(AZTEC_SCAN_API)
        response.raise_for_status()
        validators_data = response.json()
        
        exiting_validators = [
            validator["address"]
            for validator in validators_data
            if validator["status"] == 3 or validator["status"] == "EXITING"
        ]
        
        # Option 2: Fetch from contract (alternative if API is unavailable)
        if not exiting_validators:
            validators, statuses = contract.functions.getValidators().call()
            exiting_validators = [
                validators[i]
                for i in range(len(validators))
                if statuses[i] == 3
            ]
        
        return exiting_validators
    except Exception as e:
        print(f"Error fetching validators: {e}")
        return []

def finalize_validator_exit(validator_address):
    """
    Finalize the exit for a single validator.
    """
    try:
        # Build transaction
        tx = contract.functions.finalizeExit(validator_address).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,  # Adjust gas limit as needed
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id
        })

        # Sign transaction
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"Successfully finalized exit for validator {validator_address}. Tx: {tx_hash.hex()}")
        else:
            print(f"Transaction failed for validator {validator_address}. Tx: {tx_hash.hex()}")
    except Exception as e:
        print(f"Error finalizing exit for validator {validator_address}: {e}")

def main():
    # Get list of exiting validators
    exiting_validators = get_exiting_validators()
    
    if not exiting_validators:
        print("No validators with status 3 (EXITING) found.")
        return
    
    print(f"Found {len(exiting_validators)} validators to finalize exit.")
    
    # Finalize exit for each validator
    for validator in exiting_validators:
        finalize_validator_exit(validator)

if __name__ == "__main__":
    main()
