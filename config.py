# config.py

# Active network: 'testnet' or 'mainnet'
ACTIVE_NETWORK = 'testnet'

# Configuration for each network
NETWORKS = {
    'testnet': {
        'CHAIN_FILE': 'test_chain.json',
        'WALLET_FILE': 'wallet_test.json',
        'REWARD_AMOUNT': 0.5,
        'NAME': 'Testnet'
    },
    'mainnet': {
        'CHAIN_FILE': 'main_chain.json',
        'WALLET_FILE': 'wallet_main.json',
        'REWARD_AMOUNT': 2.0,
        'NAME': 'Mainnet'
    }
}

# Helper shortcuts
CHAIN_FILE = NETWORKS[ACTIVE_NETWORK]['CHAIN_FILE']
WALLET_FILE = NETWORKS[ACTIVE_NETWORK]['WALLET_FILE']
REWARD_AMOUNT = NETWORKS[ACTIVE_NETWORK]['REWARD_AMOUNT']
NETWORK_NAME = NETWORKS[ACTIVE_NETWORK]['NAME']