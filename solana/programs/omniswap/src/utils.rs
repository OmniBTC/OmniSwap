pub fn bytes_to_hex(bytes: &Vec<u8>) -> String {
	let hex_chars: [char; 16] =
		['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'];

	let mut hex_string = String::with_capacity(bytes.len() * 2);

	for byte in bytes {
		hex_string.push(hex_chars[(byte >> 4) as usize]);
		hex_string.push(hex_chars[(byte & 0xF) as usize]);
	}

	hex_string
}
