import typing
from anchorpy.error import ProgramError


class InvalidWormholeBridge(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "InvalidWormholeBridge")

    code = 6000
    name = "InvalidWormholeBridge"
    msg = "InvalidWormholeBridge"


class InvalidWormholeFeeCollector(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, "InvalidWormholeFeeCollector")

    code = 6001
    name = "InvalidWormholeFeeCollector"
    msg = "InvalidWormholeFeeCollector"


class InvalidWormholeEmitter(ProgramError):
    def __init__(self) -> None:
        super().__init__(6002, "InvalidWormholeEmitter")

    code = 6002
    name = "InvalidWormholeEmitter"
    msg = "InvalidWormholeEmitter"


class InvalidWormholeSequence(ProgramError):
    def __init__(self) -> None:
        super().__init__(6003, "InvalidWormholeSequence")

    code = 6003
    name = "InvalidWormholeSequence"
    msg = "InvalidWormholeSequence"


class InvalidSysvar(ProgramError):
    def __init__(self) -> None:
        super().__init__(6004, "InvalidSysvar")

    code = 6004
    name = "InvalidSysvar"
    msg = "InvalidSysvar"


class OwnerOnly(ProgramError):
    def __init__(self) -> None:
        super().__init__(6005, "OwnerOnly")

    code = 6005
    name = "OwnerOnly"
    msg = "OwnerOnly"


class BumpNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6006, "BumpNotFound")

    code = 6006
    name = "BumpNotFound"
    msg = "BumpNotFound"


class InvalidForeignContract(ProgramError):
    def __init__(self) -> None:
        super().__init__(6007, "InvalidForeignContract")

    code = 6007
    name = "InvalidForeignContract"
    msg = "InvalidForeignContract"


class ZeroBridgeAmount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6008, "ZeroBridgeAmount")

    code = 6008
    name = "ZeroBridgeAmount"
    msg = "ZeroBridgeAmount"


class InvalidTokenBridgeConfig(ProgramError):
    def __init__(self) -> None:
        super().__init__(6009, "InvalidTokenBridgeConfig")

    code = 6009
    name = "InvalidTokenBridgeConfig"
    msg = "InvalidTokenBridgeConfig"


class InvalidTokenBridgeAuthoritySigner(ProgramError):
    def __init__(self) -> None:
        super().__init__(6010, "InvalidTokenBridgeAuthoritySigner")

    code = 6010
    name = "InvalidTokenBridgeAuthoritySigner"
    msg = "InvalidTokenBridgeAuthoritySigner"


class InvalidTokenBridgeCustodySigner(ProgramError):
    def __init__(self) -> None:
        super().__init__(6011, "InvalidTokenBridgeCustodySigner")

    code = 6011
    name = "InvalidTokenBridgeCustodySigner"
    msg = "InvalidTokenBridgeCustodySigner"


class InvalidTokenBridgeEmitter(ProgramError):
    def __init__(self) -> None:
        super().__init__(6012, "InvalidTokenBridgeEmitter")

    code = 6012
    name = "InvalidTokenBridgeEmitter"
    msg = "InvalidTokenBridgeEmitter"


class InvalidTokenBridgeSequence(ProgramError):
    def __init__(self) -> None:
        super().__init__(6013, "InvalidTokenBridgeSequence")

    code = 6013
    name = "InvalidTokenBridgeSequence"
    msg = "InvalidTokenBridgeSequence"


class InvalidTokenBridgeSender(ProgramError):
    def __init__(self) -> None:
        super().__init__(6014, "InvalidTokenBridgeSender")

    code = 6014
    name = "InvalidTokenBridgeSender"
    msg = "InvalidTokenBridgeSender"


class InvalidRecipient(ProgramError):
    def __init__(self) -> None:
        super().__init__(6015, "InvalidRecipient")

    code = 6015
    name = "InvalidRecipient"
    msg = "InvalidRecipient"


class InvalidTransferTokenAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6016, "InvalidTransferTokenAccount")

    code = 6016
    name = "InvalidTransferTokenAccount"
    msg = "InvalidTransferTokenAccount"


class InvalidTransferToChain(ProgramError):
    def __init__(self) -> None:
        super().__init__(6017, "InvalidTransferTokenChain")

    code = 6017
    name = "InvalidTransferToChain"
    msg = "InvalidTransferTokenChain"


class InvalidTransferTokenChain(ProgramError):
    def __init__(self) -> None:
        super().__init__(6018, "InvalidTransferTokenChain")

    code = 6018
    name = "InvalidTransferTokenChain"
    msg = "InvalidTransferTokenChain"


class InvalidRelayerFee(ProgramError):
    def __init__(self) -> None:
        super().__init__(6019, "InvalidRelayerFee")

    code = 6019
    name = "InvalidRelayerFee"
    msg = "InvalidRelayerFee"


class InvalidPayerAta(ProgramError):
    def __init__(self) -> None:
        super().__init__(6020, "InvalidPayerAta")

    code = 6020
    name = "InvalidPayerAta"
    msg = "InvalidPayerAta"


class InvalidTransferToAddress(ProgramError):
    def __init__(self) -> None:
        super().__init__(6021, "InvalidTransferToAddress")

    code = 6021
    name = "InvalidTransferToAddress"
    msg = "InvalidTransferToAddress"


class AlreadyRedeemed(ProgramError):
    def __init__(self) -> None:
        super().__init__(6022, "AlreadyRedeemed")

    code = 6022
    name = "AlreadyRedeemed"
    msg = "AlreadyRedeemed"


class InvalidTokenBridgeForeignEndpoint(ProgramError):
    def __init__(self) -> None:
        super().__init__(6023, "InvalidTokenBridgeForeignEndpoint")

    code = 6023
    name = "InvalidTokenBridgeForeignEndpoint"
    msg = "InvalidTokenBridgeForeignEndpoint"


class NonExistentRelayerAta(ProgramError):
    def __init__(self) -> None:
        super().__init__(6024, "NonExistentRelayerAta")

    code = 6024
    name = "NonExistentRelayerAta"
    msg = "NonExistentRelayerAta"


class InvalidTokenBridgeMintAuthority(ProgramError):
    def __init__(self) -> None:
        super().__init__(6025, "InvalidTokenBridgeMintAuthority")

    code = 6025
    name = "InvalidTokenBridgeMintAuthority"
    msg = "InvalidTokenBridgeMintAuthority"


class InvalidDataLength(ProgramError):
    def __init__(self) -> None:
        super().__init__(6026, "InvalidDataLength")

    code = 6026
    name = "InvalidDataLength"
    msg = "InvalidDataLength"


class DeserializeSoSwapMessageFail(ProgramError):
    def __init__(self) -> None:
        super().__init__(6027, "DeserializeSoSwapMessageFail")

    code = 6027
    name = "DeserializeSoSwapMessageFail"
    msg = "DeserializeSoSwapMessageFail"


class InvalidBeneficiary(ProgramError):
    def __init__(self) -> None:
        super().__init__(6028, "InvalidBeneficiary")

    code = 6028
    name = "InvalidBeneficiary"
    msg = "InvalidBeneficiary"


class CheckFeeFail(ProgramError):
    def __init__(self) -> None:
        super().__init__(6029, "CheckFeeFail")

    code = 6029
    name = "CheckFeeFail"
    msg = "CheckFeeFail"


class UnexpectValue(ProgramError):
    def __init__(self) -> None:
        super().__init__(6030, "UnexpectValue")

    code = 6030
    name = "UnexpectValue"
    msg = "UnexpectValue"


class InvalidCallData(ProgramError):
    def __init__(self) -> None:
        super().__init__(6031, "InvalidCallData")

    code = 6031
    name = "InvalidCallData"
    msg = "InvalidCallData"


class InvalidProxy(ProgramError):
    def __init__(self) -> None:
        super().__init__(6032, "InvalidProxy")

    code = 6032
    name = "InvalidProxy"
    msg = "InvalidProxy"


CustomError = typing.Union[
    InvalidWormholeBridge,
    InvalidWormholeFeeCollector,
    InvalidWormholeEmitter,
    InvalidWormholeSequence,
    InvalidSysvar,
    OwnerOnly,
    BumpNotFound,
    InvalidForeignContract,
    ZeroBridgeAmount,
    InvalidTokenBridgeConfig,
    InvalidTokenBridgeAuthoritySigner,
    InvalidTokenBridgeCustodySigner,
    InvalidTokenBridgeEmitter,
    InvalidTokenBridgeSequence,
    InvalidTokenBridgeSender,
    InvalidRecipient,
    InvalidTransferTokenAccount,
    InvalidTransferToChain,
    InvalidTransferTokenChain,
    InvalidRelayerFee,
    InvalidPayerAta,
    InvalidTransferToAddress,
    AlreadyRedeemed,
    InvalidTokenBridgeForeignEndpoint,
    NonExistentRelayerAta,
    InvalidTokenBridgeMintAuthority,
    InvalidDataLength,
    DeserializeSoSwapMessageFail,
    InvalidBeneficiary,
    CheckFeeFail,
    UnexpectValue,
    InvalidCallData,
    InvalidProxy,
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: InvalidWormholeBridge(),
    6001: InvalidWormholeFeeCollector(),
    6002: InvalidWormholeEmitter(),
    6003: InvalidWormholeSequence(),
    6004: InvalidSysvar(),
    6005: OwnerOnly(),
    6006: BumpNotFound(),
    6007: InvalidForeignContract(),
    6008: ZeroBridgeAmount(),
    6009: InvalidTokenBridgeConfig(),
    6010: InvalidTokenBridgeAuthoritySigner(),
    6011: InvalidTokenBridgeCustodySigner(),
    6012: InvalidTokenBridgeEmitter(),
    6013: InvalidTokenBridgeSequence(),
    6014: InvalidTokenBridgeSender(),
    6015: InvalidRecipient(),
    6016: InvalidTransferTokenAccount(),
    6017: InvalidTransferToChain(),
    6018: InvalidTransferTokenChain(),
    6019: InvalidRelayerFee(),
    6020: InvalidPayerAta(),
    6021: InvalidTransferToAddress(),
    6022: AlreadyRedeemed(),
    6023: InvalidTokenBridgeForeignEndpoint(),
    6024: NonExistentRelayerAta(),
    6025: InvalidTokenBridgeMintAuthority(),
    6026: InvalidDataLength(),
    6027: DeserializeSoSwapMessageFail(),
    6028: InvalidBeneficiary(),
    6029: CheckFeeFail(),
    6030: UnexpectValue(),
    6031: InvalidCallData(),
    6032: InvalidProxy(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
