# Why These Solana & Anchor Rules Exist

### 1. Why store and verify the canonical bump?
`Pubkey::find_program_address` iterates bumps downwards from 255 until a valid off-curve address is found. Doing this repeatedly inside on-chain instructions wastes precious compute units (often 1,000–3,000 CUs per derivation). Storing the canonical bump at initialization and passing `bump = vault.bump` enables constant-time validation (`create_program_address`).

### 2. Why ban raw arithmetic operators?
Rust in debug mode panics on overflow, but in standard Solana on-chain BPF builds, unchecked arithmetic operations can wrap around silently in production, allowing attackers to mint trillions of tokens from an underflowed decrement.

### 3. Why validate CPI Program IDs?
Failing to verify the program ID of an external account passed for CPI allows an attacker to substitute a malicious mock token program that registers fake deposits.
