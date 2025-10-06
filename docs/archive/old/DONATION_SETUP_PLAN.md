# Crypto Donation Setup Plan

## Overview
Set up cryptocurrency donations for ChinaXiv Translations to support the project's ongoing development and maintenance.

## Supported Cryptocurrencies
- **Bitcoin (BTC)**
- **Ethereum (ETH)**
- **Solana (SOL)**
- **USD Coin (USDC)**
- **Tether (USDT)**
- **Stacks (STX)**

## Implementation Steps

### 1. Create Crypto Wallets
- [ ] Set up Bitcoin wallet (Electrum, BlueWallet, or hardware wallet)
- [ ] Set up Ethereum wallet (MetaMask, Trust Wallet, or hardware wallet)
- [ ] Set up Solana wallet (Phantom, Solflare, or hardware wallet)
- [ ] Set up Stacks wallet (Hiro Wallet, Xverse)
- [ ] Get public addresses for each wallet
- [ ] Generate QR codes for each address

### 2. Create Donation Page
- [ ] Create `donation.html` template
- [ ] Add crypto wallet addresses
- [ ] Add QR codes for mobile donations
- [ ] Include donation instructions
- [ ] Add tax deduction information (if applicable)
- [ ] Style consistently with site theme

### 3. Add Donation Links
- [ ] Add "Please support us by donating here" link to:
  - [ ] Main index page
  - [ ] Footer section
  - [ ] About page (if exists)
- [ ] Link should point to `/donation.html`

### 4. Update Documentation
- [ ] Add crypto donation section to README.md
- [ ] Include wallet addresses in README
- [ ] Add donation information to project documentation

### 5. Security Considerations
- [ ] Use hardware wallets for large amounts
- [ ] Enable 2FA on all wallets
- [ ] Keep private keys offline
- [ ] Consider multisig setup for larger donations
- [ ] Regular security audits

## Donation Page Content

### Header
"Support ChinaXiv Translations"

### Description
"Help us continue translating Chinese academic papers to English. Your donations support server costs, API fees, and ongoing development."

### Cryptocurrency Options
- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- USD Coin (USDC)
- Tether (USDT)
- Stacks (STX)

### Instructions
1. Copy the wallet address
2. Send your donation
3. Keep transaction receipt for tax purposes

### QR Codes
Include QR codes for each wallet address for easy mobile donations.

## Files to Create/Modify
- `src/templates/donation.html` - Donation page template
- `README.md` - Add donation section
- `src/templates/base.html` - Add donation link to footer
- `src/templates/index.html` - Add donation link to main page

## Testing
- [ ] Test donation page loads correctly
- [ ] Verify all wallet addresses are correct
- [ ] Test QR codes scan properly
- [ ] Check mobile responsiveness
- [ ] Verify links work from main pages

## Future Enhancements
- [ ] Add donation tracking/analytics
- [ ] Implement donation goals/progress bars
- [ ] Add recurring donation options
- [ ] Integrate with payment processors (Charge, SpectroCoin)
- [ ] Add GitHub Sponsors integration
