module omniswap::cross {
    use omniswap::serde;
    use omniswap::u256::{U256, Self};
    use std::vector;

    const EINVALID_LENGTH: u64 = 0x00;

    struct SoData has drop {
        // unique identification id. length is 32.
        transaction_id: vector<u8>,
        // token receiving account. length is 20, 32.
        receiver: vector<u8>,
        // source chain id
        source_chainId: u64,
        // The starting token address of the source chain
        sending_asset_id: vector<u8>,
        // destination chain id
        destination_chain_id: u64,
        // The final token address of the destination chain
        receiving_asset_id: vector<u8>,
        // User enters amount
        amount: U256
    }

    struct SwapData has drop {
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

    public entry fun encode_payload(so_data: SoData, swap_data: vector<SwapData>): vector<u8> {
        let data = vector::empty<u8>();
        serde::serialize_vector_with_length(&mut data, so_data.transaction_id);
        serde::serialize_vector_with_length(&mut data, so_data.receiver);
        serde::serialize_u64(&mut data, so_data.source_chainId);
        serde::serialize_vector_with_length(&mut data, so_data.sending_asset_id);
        serde::serialize_u64(&mut data, so_data.destination_chain_id);
        serde::serialize_vector_with_length(&mut data, so_data.receiving_asset_id);
        serde::serialize_u256(&mut data, so_data.amount);
        vector::reverse(&mut swap_data);
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

    public entry fun decode_payload(data: &mut vector<u8>): (SoData, vector<SwapData>) {
        let len = vector::length(data);
        assert!(len>0, EINVALID_LENGTH);
        let index = 0;
        let so_data = SoData {
            transaction_id: vector::empty(),
            receiver: vector::empty(),
            source_chainId: 0,
            sending_asset_id: vector::empty(),
            destination_chain_id: 0,
            receiving_asset_id: vector::empty(),
            amount: u256::zero()
        };
        let swap_data = vector::empty<SwapData>();
        so_data.transaction_id = serde::deserialize_vector_with_length(data);

        index = index + vector::length(&so_data.transaction_id);
        so_data.receiver = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

        index = index + vector::length(&so_data.receiver);
        so_data.source_chainId = serde::deserialize_u64(&serde::vector_slice(data, index, len));

        index = index + 8;
        so_data.sending_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

        index = index + vector::length(&so_data.sending_asset_id);
        so_data.destination_chain_id = serde::deserialize_u64(&serde::vector_slice(data, index, len));

        index = index + 8;
        so_data.receiving_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

        index = index + vector::length(&so_data.receiving_asset_id);
        so_data.amount = serde::deserialize_u256(&serde::vector_slice(data, index, len));

        index = index + 8;

        while (index < len) {
            let d = SwapData {
                call_to: vector::empty(),
                approve_to: vector::empty(),
                sending_asset_id: vector::empty(),
                receiving_asset_id: vector::empty(),
                from_amount: u256::zero(),
                call_data: vector::empty()
            };
            d.call_to = serde::deserialize_vector_with_length(data);

            index = index + vector::length(&d.call_to);
            d.approve_to = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

            index = index + vector::length(&d.approve_to);
            d.sending_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

            index = index + vector::length(&d.sending_asset_id);
            d.receiving_asset_id = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

            index = index + vector::length(&d.receiving_asset_id);
            d.from_amount = serde::deserialize_u256(&serde::vector_slice(data, index, len));

            index = index + 8;
            d.call_data = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));
        };

        (so_data, swap_data)
    }

    // todo! test
}
