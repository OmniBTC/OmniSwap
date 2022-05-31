pragma abicoder v2;
import "../interfaces/IStargate.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";


contract StargateTest {
    constructor() {}

    function swap(
        address routerAddress,
        uint16 _dstChainId,
        uint256 _srcPoolId,
        uint256 _dstPoolId,
        uint256 _amountLD,
        uint256 _minAmountLD,
        address usd
    ) public payable {
        _safeTransferFrom(usd, msg.sender, address(this), _amountLD);
        IERC20(usd).approve(routerAddress, _amountLD);
        IStargate(routerAddress).swap{value : msg.value}(
            _dstChainId, // send to Fuji (use LayerZero chainId)
            _srcPoolId, // source pool id
            _dstPoolId, // dest pool id
            msg.sender, // refund adddress. extra gas (if any) is returned to this address
            _amountLD, // quantity to swap
            _minAmountLD, // the min qty you would accept on the destination
            IStargate.lzTxObj(0, 0, "0x"), // 0 additional gasLimit increase, 0 airdrop, at 0x address
            abi.encodePacked(msg.sender), // the address to send the tokens to on the destination
            bytes("")                        // bytes param, if you wish to send additional payload you can abi.encode() them here
        );
    }

    function _safeTransferFrom(
        address token,
        address from,
        address to,
        uint256 value
    ) private {
        // bytes4(keccak256(bytes('transferFrom(address,address,uint256)')));
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0x23b872dd, from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "Stargate: TRANSFER_FROM_FAILED");
    }
}

