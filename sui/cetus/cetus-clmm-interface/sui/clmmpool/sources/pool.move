module cetus_clmm::pool {
    use sui::object::{ID, UID};
    use sui::balance::Balance;
    use sui::clock::Clock;
    use sui::tx_context::TxContext;
    use std::string::String;
    use integer_mate::i32::I32;
    use cetus_clmm::config::GlobalConfig;
    use cetus_clmm::position::{Position, PositionManager};
    use cetus_clmm::tick::TickManager;
    use cetus_clmm::rewarder::{RewarderManager, RewarderGlobalVault};
    use cetus_clmm::partner::Partner;

    /// The clmmpool
    struct Pool<phantom CoinTypeA, phantom CoinTypeB> has key, store {
        id: UID,

        coin_a: Balance<CoinTypeA>,
        coin_b: Balance<CoinTypeB>,

        /// The tick spacing
        tick_spacing: u32,

        /// The numerator of fee rate, the denominator is 1_000_000.
        fee_rate: u64,

        /// The liquidity of current tick index
        liquidity: u128,

        /// The current sqrt price
        current_sqrt_price: u128,

        /// The current tick index
        current_tick_index: I32,

        /// The global fee growth of coin a,b as Q64.64
        fee_growth_global_a: u128,
        fee_growth_global_b: u128,

        /// The amounts of coin a,b owend to protocol
        fee_protocol_coin_a: u64,
        fee_protocol_coin_b: u64,

        /// The tick manager
        tick_manager: TickManager,

        /// The rewarder manager
        rewarder_manager: RewarderManager,

        /// The position manager
        position_manager: PositionManager,

        /// is the pool pause
        is_pause: bool,

        /// The pool index
        index: u64,

        /// The url for pool and postion
        url: String,
    }

    // === Public Functions ===
    public fun open_position<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        tick_lower: u32,
        tick_upper: u32,
        ctx: &mut TxContext
    ): Position {
        abort 0
    }

    /// Flash loan resource for add_liquidity
    struct AddLiquidityReceipt<phantom CoinTypeA, phantom CoinTypeB> {
        pool_id: ID,
        amount_a: u64,
        amount_b: u64
    }

    public fun add_liquidity<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: &mut Position,
        delta_liquidity: u128,
        clock: &Clock,
    ): AddLiquidityReceipt<CoinTypeA, CoinTypeB> {
        abort 0
    }

    public fun add_liquidity_fix_coin<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: &mut Position,
        amount: u64,
        fix_amount_a: bool,
        clock: &Clock
    ): AddLiquidityReceipt<CoinTypeA, CoinTypeB> {
        abort 0
    }

    public fun add_liquidity_pay_amount<CoinTypeA, CoinTypeB>(
        receipt: &AddLiquidityReceipt<CoinTypeA, CoinTypeB>
    ): (u64, u64) {
        abort 0
    }

    public fun repay_add_liquidity<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        balance_a: Balance<CoinTypeA>,
        balance_b: Balance<CoinTypeB>,
        receipt: AddLiquidityReceipt<CoinTypeA, CoinTypeB>
    ) {
        abort 0
    }

    public fun remove_liquidity<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: &mut Position,
        delta_liquidity: u128,
        clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>) {
        abort 0
    }

    public fun close_position<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: Position,
    ) {
        abort 0
    }

    /// Collect the fee from position.
    public fun collect_fee<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: &Position,
        recalculate: bool,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>) {
        abort 0
    }

    /// Collect rewarder
    public fun collect_reward<CoinTypeA, CoinTypeB, CoinTypeC>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        position_nft: &Position,
        vault: &mut RewarderGlobalVault,
        recalculate: bool,
        clock: &Clock
    ): Balance<CoinTypeC> {
        abort 0
    }

    /// The step swap result
    struct SwapStepResult has copy, drop, store {
        current_sqrt_price: u128,
        target_sqrt_price: u128,
        current_liquidity: u128,
        amount_in: u64,
        amount_out: u64,
        fee_amount: u64,
        remainer_amount: u64
    }

    /// The calculated swap result
    struct CalculatedSwapResult has copy, drop, store {
        amount_in: u64,
        amount_out: u64,
        fee_amount: u64,
        fee_rate: u64,
        after_sqrt_price: u128,
        is_exceed: bool,
        step_results: vector<SwapStepResult>
    }

    // Calculate Swap Result
    public fun calculate_swap_result<CoinTypeA, CoinTypeB>(
        pool: &Pool<CoinTypeA, CoinTypeB>,
        a2b: bool,
        by_amount_in: bool,
        amount: u64,
    ): CalculatedSwapResult {
        abort 0
    }

    public fun calculated_swap_result_amount_out(calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculated_swap_result_is_exceed(calculatedSwapResult: &CalculatedSwapResult): bool {
        abort 0
    }

    public fun calculated_swap_result_amount_in(calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculated_swap_result_after_sqrt_price(calculatedSwapResult: &CalculatedSwapResult): u128 {
        abort 0
    }

    public fun calculated_swap_result_fee_amount(calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculate_swap_result_step_results(calculatedSwapResult: &CalculatedSwapResult): &vector<SwapStepResult> {
        abort 0
    }

    public fun calculated_swap_result_steps_length(calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }



    /// Flash loan resource for swap.
    /// There is no way in Move to pass calldata and make dynamic calls, but a resource can be used for this purpose.
    /// To make the execution into a single transaction, the flash loan function must return a resource
    /// that cannot be copied, cannot be saved, cannot be dropped, or cloned.
    struct FlashSwapReceipt<phantom CoinTypeA, phantom CoinTypeB> {
        pool_id: ID,
        a2b: bool,
        partner_id: ID,
        pay_amount: u64,
        ref_fee_amount: u64
    }

    /// Flash swap
    public fun flash_swap<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        a2b: bool,
        by_amount_in: bool,
        amount: u64,
        sqrt_price_limit: u128,
        clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>, FlashSwapReceipt<CoinTypeA, CoinTypeB>) {
        abort 0
    }

    /// Flash swap with partner
    public fun flash_swap_with_partner<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        partner: &Partner,
        a2b: bool,
        by_amount_in: bool,
        amount: u64,
        sqrt_price_limit: u128,
        clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>, FlashSwapReceipt<CoinTypeA, CoinTypeB>) {
        abort 0
    }

    /// Repay for flash swap
    public fun repay_flash_swap<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        coin_a: Balance<CoinTypeA>,
        coin_b: Balance<CoinTypeB>,
        receipt: FlashSwapReceipt<CoinTypeA, CoinTypeB>
    ) {
        abort 0
    }

    /// Repay for flash swap with partner for receive ref fee.
    public fun repay_flash_swap_with_partner<CoinTypeA, CoinTypeB>(
        config: &GlobalConfig,
        pool: &mut Pool<CoinTypeA, CoinTypeB>,
        partner: &mut Partner,
        coin_a: Balance<CoinTypeA>,
        coin_b: Balance<CoinTypeB>,
        receipt: FlashSwapReceipt<CoinTypeA, CoinTypeB>
    )  {
        abort 0
    }

    /// Get the swap pay amount
    public fun swap_pay_amount<CoinTypeA, CoinTypeB>(receipt: &FlashSwapReceipt<CoinTypeA, CoinTypeB>): u64 {
        abort 0
    }
}