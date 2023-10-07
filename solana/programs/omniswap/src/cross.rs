use spl_math::uint::U256;

use super::serde;

#[derive(PartialEq, Debug, Clone)]
pub struct NormalizedSoData {
    // Unique identification id. length is 32.
    pub transaction_id: Vec<u8>,
    // Token receiving account. length is 20, 32.
    pub receiver: Vec<u8>,
    // Source chain id
    pub source_chain_id: u16,
    // The starting token address of the source chain
    pub sending_asset_id: Vec<u8>,
    // Destination chain id
    pub destination_chain_id: u16,
    // The final token address of the destination chain
    pub receiving_asset_id: Vec<u8>,
    // User enters amount
    pub amount: U256
}

#[derive(PartialEq, Debug, Clone)]
pub struct NormalizedSwapData {
    // The swap address
    pub call_to: Vec<u8>,
    // The swap address
    pub approve_to: Vec<u8>,
    // The swap start token address
    pub sending_asset_id: Vec<u8>,
    // The swap final token address
    pub receiving_asset_id: Vec<u8>,
    // The swap start token amount
    pub from_amount: U256,
    // The swap callData
    pub call_data: Vec<u8>
}

#[derive(PartialEq, Debug, Clone)]
pub struct NormalizedWormholeData {
    // destination wormhole chain id
    pub dst_wormhole_chain_id: u16,
    // gas price of the target chain
    pub dst_max_gas_price_in_wei_for_relayer: U256,
    // payment required for aptos coin
    pub wormhole_fee: U256,
    // destination chain sodiamond address
    pub dst_so_diamond: Vec<u8>,
}

impl NormalizedSoData {
    pub fn padding_so_data(
        transaction_id: Vec<u8>,
        receiver: Vec<u8>,
        receiving_asset_id: Vec<u8>
    ) -> Self {
        NormalizedSoData {
            transaction_id,
            receiver,
            source_chain_id: 0,
            sending_asset_id: Vec::new(),
            destination_chain_id: 0,
            receiving_asset_id,
            amount: U256::zero()
        }
    }
    pub fn encode_normalized_so_data(so_data: NormalizedSoData) -> Vec<u8> {
        let mut data = Vec::<u8>::new();
        serde::serialize_vector_with_length(&mut data, &so_data.transaction_id);
        serde::serialize_vector_with_length(&mut data, &so_data.receiver);
        serde::serialize_u16(&mut data, so_data.source_chain_id);
        serde::serialize_vector_with_length(&mut data, &so_data.sending_asset_id);
        serde::serialize_u16(&mut data, so_data.destination_chain_id);
        serde::serialize_vector_with_length(&mut data, &so_data.receiving_asset_id);
        serde::serialize_u256(&mut data, so_data.amount);
        data
    }

    pub fn decode_normalized_so_data(data: &[u8]) -> Self {
        let data_len = data.len();
        assert!(data_len > 0, "EINVALID_LENGTH");

        let mut index = 0;
        let mut next_len;

        next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
        let transaction_id = serde::deserialize_vector_with_length(&data[index..index + next_len]);
        index = index + next_len;

        next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
        let receiver = serde::deserialize_vector_with_length(&data[index..index + next_len]);
        index = index + next_len;

        next_len = 2;
        let source_chain_id = serde::deserialize_u16(&data[index..index + next_len]);
        index = index + next_len;

        next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
        let sending_asset_id = serde::deserialize_vector_with_length(&data[index..index + next_len]);
        index = index + next_len;

        next_len = 2;
        let destination_chain_id = serde::deserialize_u16(&data[index..index + next_len]);
        index = index + next_len;

        next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
        let receiving_asset_id = serde::deserialize_vector_with_length(&data[index..index + next_len]);
        index = index + next_len;

        next_len = 32;
        let amount = serde::deserialize_u256(&data[index..index + next_len]);
        index = index + next_len;

        assert_eq!(index, data_len, "EINVALID_LENGTH");

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
}


impl NormalizedSwapData {
    pub fn padding_swap_data(
        call_to: Vec<u8>,
        sending_asset_id: Vec<u8>,
        receiving_asset_id: Vec<u8>,
        call_data: Vec<u8>
    ) -> Self {
        NormalizedSwapData {
            call_to: call_to.clone(),
            approve_to: call_to,
            sending_asset_id,
            receiving_asset_id,
            from_amount: U256::zero(),
            call_data
        }
    }

    pub fn encode_normalized_swap_data(swap_data: &Vec<NormalizedSwapData>) -> Vec<u8> {
        let mut data = Vec::<u8>::new();

        let swap_len = swap_data.len();
        if swap_len > 0 {
            serde::serialize_u64(&mut data, swap_len as u64)
        };

        for d in swap_data {
            serde::serialize_vector_with_length(&mut data, &d.call_to);
            serde::serialize_vector_with_length(&mut data, &d.approve_to);
            serde::serialize_vector_with_length(&mut data, &d.sending_asset_id);
            serde::serialize_vector_with_length(&mut data, &d.receiving_asset_id);
            serde::serialize_u256(&mut data, d.from_amount);
            serde::serialize_vector_with_length(&mut data, &d.call_data);
        };

        data
    }

    pub fn decode_normalized_swap_data(data: &[u8]) -> Vec<NormalizedSwapData> {
        let data_len = data.len();
        assert!(data_len > 0, "EINVALID_LENGTH");
        let mut index = 0;
        let mut next_len;
        let mut swap_data = Vec::<NormalizedSwapData>::new();

        next_len = 8;
        let _swap_len = serde::deserialize_u64(&data[index..index + next_len]);
        index = index + next_len;

        while index < data_len {
            next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
            let call_to = serde::deserialize_vector_with_length(&data[index..index + next_len]);
            index = index + next_len;

            next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
            let approve_to = serde::deserialize_vector_with_length(&data[index..index + next_len]);
            index = index + next_len;

            next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
            let sending_asset_id = serde::deserialize_vector_with_length(&data[index..index + next_len]);
            index = index + next_len;

            next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
            let receiving_asset_id = serde::deserialize_vector_with_length(&data[index..index + next_len]);
            index = index + next_len;

            next_len = 32;
            let from_amount = serde::deserialize_u256(&data[index..index + next_len]);
            index = index + next_len;

            next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
            let call_data = serde::deserialize_vector_with_length(&data[index..index + next_len]);
            index = index + next_len;

            swap_data.push(NormalizedSwapData {
                call_to,
                approve_to,
                sending_asset_id,
                receiving_asset_id,
                from_amount,
                call_data
            });
        };

        assert!(index == data_len, "EINVALID_LENGTH");

        swap_data
    }
}


impl NormalizedWormholeData {
    pub fn encode_normalized_wormhole_data(wormhole_data: &NormalizedWormholeData) -> Vec<u8> {
        let mut data = Vec::<u8>::new();

        serde::serialize_u16(&mut data, wormhole_data.dst_wormhole_chain_id);
        serde::serialize_u256(&mut data, wormhole_data.dst_max_gas_price_in_wei_for_relayer);
        serde::serialize_u256(&mut data, wormhole_data.wormhole_fee);
        serde::serialize_vector_with_length(&mut data, &wormhole_data.dst_so_diamond);
        data
    }

    pub fn decode_normalized_wormhole_data(data: &[u8]) -> Self {
        let data_len = data.len();
        assert!(data_len > 0, "EINVALID_LENGTH");
        let mut index = 0;
        let mut next_len;

        next_len = 2;
        let dst_wormhole_chain_id = serde::deserialize_u16(&data[index..index + next_len]);
        index = index + next_len;

        next_len = 32;
        let dst_max_gas_price_in_wei_for_relayer = serde::deserialize_u256(&data[index..index + next_len]);
        index = index + next_len;

        next_len = 32;
        let wormhole_fee = serde::deserialize_u256(&data[index..index + next_len]);
        index = index + next_len;

        next_len = (8 + serde::get_vector_length(&data[index..index + 8])) as usize;
        let dst_so_diamond = serde::deserialize_vector_with_length(&data[index..index + next_len]);
        index = index + next_len;

        assert!(index == data_len, "EINVALID_LENGTH");

        NormalizedWormholeData {
            dst_wormhole_chain_id,
            dst_max_gas_price_in_wei_for_relayer,
            wormhole_fee,
            dst_so_diamond
        }
    }
}

#[cfg(test)]
pub mod test {
    use hex_literal::hex;
    use super::*;

    #[test]
    fn test_wormhole_data() {
        let wormhole_data = NormalizedWormholeData {
            dst_wormhole_chain_id: 1,
            dst_max_gas_price_in_wei_for_relayer: U256::from(10000u32),
            wormhole_fee: U256::from(2389u32),
            dst_so_diamond: hex!("2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af").to_vec()
        };
        let encode_data = NormalizedWormholeData::encode_normalized_wormhole_data(&wormhole_data);

        let data = hex!("00010000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000095500000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af").to_vec();

        assert_eq!(data, encode_data);
        assert_eq!(NormalizedWormholeData::decode_normalized_wormhole_data(&data), wormhole_data);
    }

    #[test]
    fn test_serde_so_data() {
        let so_data = NormalizedSoData {
            transaction_id: hex!("4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed").to_vec(),
            receiver: hex!("2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af").to_vec(),
            source_chain_id: 1,
            sending_asset_id: b"0x1::aptos_coin::AptosCoin".to_vec(),
            destination_chain_id: 2,
            receiving_asset_id: hex!("957Eb0316f02ba4a9De3D308742eefd44a3c1719").to_vec(),
            amount: 100000000.into()
        };
        let encode_data = NormalizedSoData::encode_normalized_so_data(so_data.clone());
        let data = hex!("00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100").to_vec();

        assert_eq!(data, encode_data);
        assert_eq!(NormalizedSoData::decode_normalized_so_data(&data), so_data);
    }

    #[test]
    fn test_serde_swap_data() {
        let swap_data = vec![
            NormalizedSwapData {
                call_to: hex!("4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81").to_vec(),
                approve_to: hex!("4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81").to_vec(),
                sending_asset_id: b"0x1::aptos_coin::AptosCoin".to_vec(),
                receiving_asset_id: b"0x1::omni_bridge::XBTC".to_vec(),
                from_amount: 8900000000u128.into(),
                // liquidswap curve
                call_data: b"0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81::curves::Uncorrelated".to_vec()
            },
            NormalizedSwapData {
                call_to: hex!("957Eb0316f02ba4a9De3D308742eefd44a3c1719").to_vec(),
                approve_to: hex!("957Eb0316f02ba4a9De3D308742eefd44a3c1719").to_vec(),
                sending_asset_id: hex!("2514895c72f50d8bd4b4f9b1110f0d6bd2c97526").to_vec(),
                receiving_asset_id: hex!("143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7").to_vec(),
                from_amount: 7700000000u128.into(),
                // liquidswap curve
                call_data: hex!("6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7").to_vec()
            }
        ];

        let encode_data = NormalizedSwapData::encode_normalized_swap_data(&swap_data);
        let data = hex!("000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7").to_vec();

        assert_eq!(data, encode_data);
        assert_eq!(NormalizedSwapData::decode_normalized_swap_data(&data), swap_data);
    }
}