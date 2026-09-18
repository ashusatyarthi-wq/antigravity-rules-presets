# Antigravity Preset: Solana & Anchor Smart Contract Development

This configuration hardens Google Antigravity agents generating and auditing Solana programs using Anchor, Rust, and TypeScript test suites.

---

## 1. Account Validation & Security Constraints
- **PDA Canonical Bump Verification**:
  - Always store the canonical `bump` in the account data on initialization.
  - When referencing existing PDAs, pass the stored bump in the Anchor attribute:
    ```rust
    #[account(
        mut,
        seeds = [b"vault", authority.key().as_ref()],
        bump = vault.bump
    )]
    pub vault: Account<'info, VaultAccount>,
    ```
  - Never call `find_program_address` inside on-chain instruction handlers if the bump can be supplied, preserving critical compute units.
- **Strict Ownership & Authority Verification**:
  - Use `has_one = authority @ ErrorCode::Unauthorized` on state accounts rather than manual `if vault.authority != *authority.key` checks.
  - Mark accounts mutable (`mut`) ONLY when their state or lamport balance is mutated in the instruction.

---

## 2. Arithmetic & Financial Invariants
- **Checked Math Everywhere**:
  - Ban all native arithmetic operators (`+`, `-`, `*`, `/`) on token amounts and balances.
  - Always use checked equivalents with explicit custom errors:
    ```rust
    let new_balance = vault.balance.checked_add(amount).ok_or(ErrorCode::MathOverflow)?;
    ```
- **CPI Re-entrancy & Remaining Accounts**:
  - Verify CPI targets against hardcoded or config-validated program IDs (e.g. `token_program.key == &anchor_spl::token::ID`).

---

## 3. Verification Protocol
1. Build program in release mode: `anchor build`
2. Run local validator test harness:
   ```bash
   anchor test --skip-local-validator
   ```
3. Run compute unit inspection: Verify instruction cost remains well below the 200,000 CU limit.
