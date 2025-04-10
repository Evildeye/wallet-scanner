import os
import time
import hashlib
import sys
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins
from web3 import Web3
import requests
from tqdm import tqdm
import json

# Termux-specific configuration
TERMUX_MODE = True  # Enable Termux optimizations
RESULTS_FILE = "wallet_results.json"
MIN_BALANCE = 0.00001  # Minimum balance to consider

# Blockchain configuration
CONFIG = {
    'eth': {
        'provider': 'https://mainnet.infura.io/v3/d3011414c0114807911c1b6cea9d79f4',
        'scan_api': 'https://api.etherscan.io/api',
        'api_key': 'V6IVNYQX5GT6449MZ7CSI4IY5CKB2VZ64J',
        'symbol': 'ETH'
    },
    'bsc': {
        'provider': 'https://bsc-dataseed.binance.org/',
        'scan_api': 'https://api.bscscan.com/api',
        'api_key': '7TE7WEGMD443RZJ9I1BDHVEFB5FEIKD6W9',
        'symbol': 'BNB'
    }
}

class TermuxWalletScanner:
    def __init__(self):
        self.checked_seeds = set()
        self.valid_wallets = []
        self.load_progress()

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear')

    def save_progress(self):
        """Save results to file"""
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                'checked_seeds': list(self.checked_seeds),
                'valid_wallets': self.valid_wallets
            }, f)

    def load_progress(self):
        """Load previous progress"""
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r') as f:
                data = json.load(f)
                self.checked_seeds = set(data.get('checked_seeds', []))
                self.valid_wallets = data.get('valid_wallets', [])

    def generate_seed(self, word_count=12):
        """Generate unique seed phrase"""
        while True:
            seed = Bip39MnemonicGenerator().FromWordsNumber(word_count).ToStr()
            seed_hash = hashlib.sha256(seed.encode()).hexdigest()
            if seed_hash not in self.checked_seeds:
                self.checked_seeds.add(seed_hash)
                return seed

    def get_address(self, seed):
        """Derive address from seed"""
        seed_bytes = Bip39SeedGenerator(seed).Generate()
        bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        return bip44_mst_ctx.PublicKey().ToAddress()

    def check_balance(self, address, chain):
        """Check native token balance"""
        try:
            w3 = Web3(Web3.HTTPProvider(CONFIG[chain]['provider']))
            balance = w3.from_wei(w3.eth.get_balance(address), 'ether')
            return balance if balance >= MIN_BALANCE else 0
        except Exception as e:
            print(f"\n⚠️ Error checking {chain} balance: {str(e)}")
            return 0

    def scan_wallet(self, seed, address):
        """Scan wallet across all chains"""
        balances = {}
        for chain in CONFIG:
            balance = self.check_balance(address, chain)
            if balance > 0:
                balances[chain] = {
                    'symbol': CONFIG[chain]['symbol'],
                    'balance': balance
                }
        return balances if balances else None

    def display_wallet(self, seed, address, balances=None):
        """Display wallet info with Termux optimizations"""
        if balances:
            self.valid_wallets.append({
                'seed': seed,
                'address': address,
                'balances': balances
            })
            print("\n" + "="*40)
            print(f"💰 WALLET WITH BALANCE")
            print(f"🔑 Seed: {seed}")
            print(f"📍 Address: {address}")
            for chain, bal in balances.items():
                print(f"  {bal['symbol']}: {bal['balance']:.8f}")
            print("="*40)
        elif TERMUX_MODE:
            print(f"\n🔍 Scanning: {address[:8]}...{address[-6:]}")
            time.sleep(1)
            sys.stdout.write("\033[F\033[K")  # Clear previous line

    def show_summary(self):
        """Display final results"""
        self.clear_screen()
        print("\n" + "="*40)
        print("📊 SCAN SUMMARY")
        print(f"🔢 Total scanned: {len(self.checked_seeds)}")
        print(f"💰 With balance: {len(self.valid_wallets)}")
        print("="*40)
        
        if self.valid_wallets:
            print("\n💎 VALID WALLETS:")
            for i, wallet in enumerate(self.valid_wallets, 1):
                print(f"\n🆔 Wallet #{i}")
                print(f"🔑 {wallet['seed']}")
                print(f"📍 {wallet['address']}")
                for chain, bal in wallet['balances'].items():
                    print(f"  {bal['symbol']}: {bal['balance']:.8f}")
        print("\n✅ Results saved to:", RESULTS_FILE)

    def run(self):
        """Main execution flow"""
        self.clear_screen()
        print("🚀 TERMUX WALLET SCANNER")
        print("⚡ Optimized for Android")
        print("🔍 Empty wallets auto-hide\n")
        
        try:
            word_count = int(input("Seed length (12/15/18/21/24) [12]: ") or 12)
            batch_size = int(input("Wallets to scan [20]: ") or 20)
            
            if word_count not in [12, 15, 18, 21, 24]:
                print("❌ Invalid seed length")
                return
            
            print(f"\n🔄 Scanning {batch_size} wallets...")
            
            with tqdm(total=batch_size, desc="Progress", unit="wallet", 
                     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
                for _ in range(batch_size):
                    seed = self.generate_seed(word_count)
                    address = self.get_address(seed)
                    balances = self.scan_wallet(seed, address)
                    self.display_wallet(seed, address, balances)
                    pbar.update(1)
                    time.sleep(0.5)  # Rate limiting
            
            self.save_progress()
            self.show_summary()
            
        except KeyboardInterrupt:
            print("\n🛑 Scan stopped by user")
            self.save_progress()
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    scanner = TermuxWalletScanner()
    scanner.run()
