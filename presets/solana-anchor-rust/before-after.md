# Before vs After: Solana & Anchor Rules

## Scenario: Token Vault Deposit

### Before (Unchecked Vulnerable Anchor Code)
```rust
pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    // Unchecked math can overflow
    ctx.accounts.vault.balance += amount; 
    // Manual check easily forgotten or bypassed
    if ctx.accounts.vault.owner != *ctx.accounts.user.key {
        return err!(ErrorCode::Unauthorized);
    }
    Ok(())
}
```

### After (Antigravity Hardened Rules)
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        mut,
        has_one = owner @ ErrorCode::Unauthorized,
        seeds = [b"vault", owner.key().as_ref()],
        bump = vault.bump
    )]
    pub vault: Account<'info, VaultAccount>,
    pub owner: Signer<'info>,
}

pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    ctx.accounts.vault.balance = ctx.accounts.vault.balance
        .checked_add(amount)
        .ok_or(ErrorCode::MathOverflow)?;
    Ok(())
}
```
