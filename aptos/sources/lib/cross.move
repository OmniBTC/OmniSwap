module omniswap::cross {
    use std::error;
    use std::vector;

    use omniswap::serde;
    use omniswap::u16::{U16, Self};
    use omniswap::u256::{U256, Self};

    const EINVALID_LENGTH: u64 = 0x00;

    struct NormalizedSoData has drop, copy {
        // Unique identification id. length is 32.
        transaction_id: vector<u8>,
        // Token receiving account. length is 20, 32.
        receiver: vector<u8>,
        // Source chain id
        source_chain_id: U16,
        // The starting token address of the source chain
        sending_asset_id: vector<u8>,
        // Destination chain id
        destination_chain_id: U16,
        // The final token address of the destination chain
        receiving_asset_id: vector<u8>,
        // User enters amount
        amount: U256
    }

    struct NormalizedSwapData has drop, copy {
        // The swap address
        call_to: vector<u8>,
        // The swap address
        approve_to: vector<u8>,
        // The swap start token address
        sending_asset_id: vector<u8>,
        // The swap final token address
        receiving_asset_id: vector<u8>,
        // The swap start token amount
        from_amount: U256,
        // The swap callData
        call_data: vector<u8>
    }

    /// Get Methods

    public fun so_receiver(data: NormalizedSoData): vector<u8> {
        data.receiver
    }

    public fun so_amount(data: NormalizedSoData): U256 {
        data.amount
    }

    public fun so_transaction_id(data: NormalizedSoData): vector<u8> {
        data.transaction_id
    }

    public fun so_sending_asset_id(data: NormalizedSoData): vector<u8> {
        data.sending_asset_id
    }

    public fun so_receiving_asset_id(data: NormalizedSoData): vector<u8> {
        data.receiving_asset_id
    }

    public fun swap_call_to(data: NormalizedSwapData): vector<u8> {
        data.call_to
    }

    public fun swap_sending_asset_id(data: NormalizedSwapData): vector<u8> {
        data.sending_asset_id
    }

    public fun swap_receiving_asset_id(data: NormalizedSwapData): vector<u8> {
        data.receiving_asset_id
    }

    public fun swap_call_data(data: NormalizedSwapData): vector<u8> {
        data.call_data
    }

    public fun swap_from_amount(data: NormalizedSwapData): U256 {
        data.from_amount
    }

    /// Encode && Decode

    public fun encode_normalized_so_data(so_data: NormalizedSoData): vector<u8> {
        let data = vector::empty<u8>();
        serde::serialize_vector_with_length(&mut data, so_data.transaction_id);
        serde::serialize_vector_with_length(&mut data, so_data.receiver);
        serde::serialize_u16(&mut data, so_data.source_chain_id);
        serde::serialize_vector_with_length(&mut data, so_data.sending_asset_id);
        serde::serialize_u16(&mut data, so_data.destination_chain_id);
        serde::serialize_vector_with_length(&mut data, so_data.receiving_asset_id);
        serde::serialize_u256(&mut data, so_data.amount);
        data
    }

    public fun encode_normalized_swap_data(swap_data: vector<NormalizedSwapData>): vector<u8> {
        let data = vector::empty<u8>();
        vector::reverse(&mut swap_data);

        let len = vector::length(&swap_data);
        if (len > 0) {
            serde::serialize_u64(&mut data, len)
        };

        while (!vector::is_empty(&swap_data)) {
            let d = vector::pop_back(&mut swap_data);
            serde::serialize_vector_with_length(&mut data, d.call_to);
            serde::serialize_vector_with_length(&mut data, d.approve_to);
            serde::serialize_vector_with_length(&mut data, d.sending_asset_id);
            serde::serialize_vector_with_length(&mut data, d.receiving_asset_id);
            serde::serialize_u256(&mut data, d.from_amount);
            serde::serialize_vector_with_length(&mut data, d.call_data);
        };
        data
    }

    public fun decode_normalized_so_data(data: &vector<u8>): NormalizedSoData {
        let len = vector::length(data);
        assert!(len > 0, error::invalid_argument(EINVALID_LENGTH));

        let index = 0;
        let next_len;

        next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
        let transaction_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
        let receiver = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 2;
        let source_chain_id = serde::deserialize_u16(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
        let sending_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 2;
        let destination_chain_id = serde::deserialize_u16(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
        let receiving_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 32;
        let amount = serde::deserialize_u256(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        assert!(index == len, EINVALID_LENGTH);

        NormalizedSoData {
            transaction_id,
            receiver,
            source_chain_id,
            sending_asset_id,
            destination_chain_id,
            receiving_asset_id,
            amount
        }
    }

    public fun decode_normalized_swap_data(data: &vector<u8>): vector<NormalizedSwapData> {
        let len = vector::length(data);
        assert!(len > 0, error::invalid_argument(EINVALID_LENGTH));
        let index = 0;
        let next_len;
        let swap_data = vector::empty<NormalizedSwapData>();

        next_len = 8;
        let _swap_len = serde::deserialize_u64(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        while (index < len) {
            next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
            let call_to = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
            let approve_to = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
            let sending_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
            let receiving_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            next_len = 32;
            let from_amount = serde::deserialize_u256(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
            let call_data = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
            index = index + next_len;

            vector::push_back(&mut swap_data, NormalizedSwapData {
                call_to,
                approve_to,
                sending_asset_id,
                receiving_asset_id,
                from_amount,
                call_data
            });
        };

        assert!(index == len, EINVALID_LENGTH);

        swap_data
    }

    public fun padding_so_data(transaction_id: vector<u8>, receiver: vector<u8>, receiving_asset_id: vector<u8>): NormalizedSoData {
        NormalizedSoData {
            transaction_id,
            receiver,
            source_chain_id: u16::zero(),
            sending_asset_id: vector::empty(),
            destination_chain_id: u16::zero(),
            receiving_asset_id,
            amount: u256::zero()
        }
    }

    public fun padding_swap_data(
        call_to: vector<u8>,
        sending_asset_id: vector<u8>,
        receiving_asset_id: vector<u8>,
        call_data: vector<u8>): NormalizedSwapData {
        NormalizedSwapData {
            call_to,
            approve_to: call_to,
            sending_asset_id,
            receiving_asset_id,
            from_amount: u256::zero(),
            call_data
        }
    }

    #[test_only]
    public fun construct_swap_data(
        call_to: vector<u8>,
        approve_to: vector<u8>,
        sending_asset_id: vector<u8>,
        receiving_asset_id: vector<u8>,
        from_amount: U256,
        call_data: vector<u8>
    ): NormalizedSwapData {
        NormalizedSwapData {
            call_to,
            approve_to,
            sending_asset_id,
            receiving_asset_id,
            from_amount,
            // liquidswap curve
            call_data
        }
    }

    #[test_only]
    public fun construct_so_data(
        transaction_id: vector<u8>,
        receiver: vector<u8>,
        source_chain_id: U16,
        sending_asset_id: vector<u8>,
        destination_chain_id: U16,
        receiving_asset_id: vector<u8>,
        amount: U256
    ): NormalizedSoData {
        NormalizedSoData {
            transaction_id,
            receiver,
            source_chain_id,
            sending_asset_id,
            destination_chain_id,
            receiving_asset_id,
            amount
        }
    }

    #[test]
    fun test_serde_so_data() {
        let so_data = NormalizedSoData {
            transaction_id: x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
            receiver: x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            source_chain_id: u16::from_u64(1),
            sending_asset_id: b"0x1::aptos_coin::AptosCoin",
            destination_chain_id: u16::from_u64(2),
            receiving_asset_id: x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            amount: u256::from_u64(100000000)
        };
        let encode_data = encode_normalized_so_data(so_data);
        let data = x"00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100";
        assert!(data == encode_data, 1);
        assert!(decode_normalized_so_data(&data) == so_data, 1);
    }

    #[test]
    fun test_serde_swap_data() {
        let swap_data = vector<NormalizedSwapData>[
            NormalizedSwapData {
                call_to: x"4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81",
                approve_to: x"4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81",
                sending_asset_id: b"0x1::aptos_coin::AptosCoin",
                receiving_asset_id: b"0x1::omni_bridge::XBTC",
                from_amount: u256::from_u64(8900000000),
                // liquidswap curve
                call_data: b"0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81::curves::Uncorrelated"
            },
            NormalizedSwapData {
                call_to: x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
                approve_to: x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
                sending_asset_id: x"2514895c72f50d8bd4b4f9b1110f0d6bd2c97526",
                receiving_asset_id: x"143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
                from_amount: u256::from_u64(7700000000),
                // liquidswap curve
                call_data: x"6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"
            }
        ];

        let encode_data = encode_normalized_swap_data(swap_data);
        let data = x"000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7";
        assert!(data == encode_data, 1);
        assert!(decode_normalized_swap_data(&data) == swap_data, 1);
    }
}
