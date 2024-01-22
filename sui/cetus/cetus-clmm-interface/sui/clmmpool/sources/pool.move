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
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _tick_lower: u32,
        _tick_upper: u32,
        _ctx: &mut TxContext
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
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: &mut Position,
        _delta_liquidity: u128,
        _clock: &Clock,
    ): AddLiquidityReceipt<CoinTypeA, CoinTypeB> {
        abort 0
    }

    public fun add_liquidity_fix_coin<CoinTypeA, CoinTypeB>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: &mut Position,
        _amount: u64,
        _fix_amount_a: bool,
        _clock: &Clock
    ): AddLiquidityReceipt<CoinTypeA, CoinTypeB> {
        abort 0
    }

    public fun add_liquidity_pay_amount<CoinTypeA, CoinTypeB>(
        _receipt: &AddLiquidityReceipt<CoinTypeA, CoinTypeB>
    ): (u64, u64) {
        abort 0
    }

    public fun repay_add_liquidity<CoinTypeA, CoinTypeB>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _balance_a: Balance<CoinTypeA>,
        _balance_b: Balance<CoinTypeB>,
        _receipt: AddLiquidityReceipt<CoinTypeA, CoinTypeB>
    ) {
        abort 0
    }

    public fun remove_liquidity<CoinTypeA, CoinTypeB>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: &mut Position,
        _delta_liquidity: u128,
        _clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>) {
        abort 0
    }

    public fun close_position<CoinTypeA, CoinTypeB>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: Position,
    ) {
        abort 0
    }

    /// Collect the fee from position.
    public fun collect_fee<CoinTypeA, CoinTypeB>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: &Position,
        _recalculate: bool,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>) {
        abort 0
    }

    /// Collect rewarder
    public fun collect_reward<CoinTypeA, CoinTypeB, CoinTypeC>(
        __config: &GlobalConfig,
        __pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _position_nft: &Position,
        _vault: &mut RewarderGlobalVault,
        _recalculate: bool,
        _clock: &Clock
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
        _amount_in: u64,
        _amount_out: u64,
        _fee_amount: u64,
        _fee_rate: u64,
        _after_sqrt_price: u128,
        _is_exceed: bool,
        _step_results: vector<SwapStepResult>
    }

    // Calculate Swap Result
    public fun calculate_swap_result<CoinTypeA, CoinTypeB>(
        _pool: &Pool<CoinTypeA, CoinTypeB>,
        __a2b: bool,
        _by_amount_in: bool,
        _amount: u64,
    ): CalculatedSwapResult {
        abort 0
    }

    public fun calculated_swap_result_amount_out(_calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculated_swap_result_is_exceed(_calculatedSwapResult: &CalculatedSwapResult): bool {
        abort 0
    }

    public fun calculated_swap_result_amount_in(_calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculated_swap_result_after_sqrt_price(_calculatedSwapResult: &CalculatedSwapResult): u128 {
        abort 0
    }

    public fun calculated_swap_result_fee_amount(_calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }

    public fun calculate_swap_result_step_results(_calculatedSwapResult: &CalculatedSwapResult): &vector<SwapStepResult> {
        abort 0
    }

    public fun calculated_swap_result_steps_length(_calculatedSwapResult: &CalculatedSwapResult): u64 {
        abort 0
    }



    /// Flash loan resource for swap.
    /// There is no way in Move to pass calldata and make dynamic calls, but a resource can be used for this purpose.
    /// To make the execution into a single transaction, the flash loan function must return a resource
    /// that cannot be copied, cannot be saved, cannot be dropped, or cloned.
    struct FlashSwapReceipt<phantom CoinTypeA, phantom CoinTypeB> {
        pool_id: ID,
        _a2b: bool,
        partner_id: ID,
        pay_amount: u64,
        ref_fee_amount: u64
    }

    /// Flash swap
    public fun flash_swap<CoinTypeA, CoinTypeB>(
        _config: &GlobalConfig,
        _pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _a2b: bool,
        _by_amount_in: bool,
        _amount: u64,
        _sqrt_price_limit: u128,
        _clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>, FlashSwapReceipt<CoinTypeA, CoinTypeB>) {
        abort 0
    }

    /// Flash swap with partner
    public fun flash_swap_with_partner<CoinTypeA, CoinTypeB>(
        _config: &GlobalConfig,
        _pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _partner: &Partner,
        _a2b: bool,
        _by_amount_in: bool,
        _amount: u64,
        _sqrt_price_limit: u128,
        _clock: &Clock,
    ): (Balance<CoinTypeA>, Balance<CoinTypeB>, FlashSwapReceipt<CoinTypeA, CoinTypeB>) {
        abort 0
    }

    /// Repay for flash swap
    public fun repay_flash_swap<CoinTypeA, CoinTypeB>(
        _config: &GlobalConfig,
        _pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _coin_a: Balance<CoinTypeA>,
        _coin_b: Balance<CoinTypeB>,
        _receipt: FlashSwapReceipt<CoinTypeA, CoinTypeB>
    ) {
        abort 0
    }

    /// Repay for flash swap with partner for receive ref fee.
    public fun repay_flash_swap_with_partner<CoinTypeA, CoinTypeB>(
        _config: &GlobalConfig,
        _pool: &mut Pool<CoinTypeA, CoinTypeB>,
        _partner: &mut Partner,
        _coin_a: Balance<CoinTypeA>,
        _coin_b: Balance<CoinTypeB>,
        _receipt: FlashSwapReceipt<CoinTypeA, CoinTypeB>
    )  {
        abort 0
    }

    /// Get the swap pay amount
    public fun swap_pay_amount<CoinTypeA, CoinTypeB>(_receipt: &FlashSwapReceipt<CoinTypeA, CoinTypeB>): u64 {
        abort 0
    }
}
