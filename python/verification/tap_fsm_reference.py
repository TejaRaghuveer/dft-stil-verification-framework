"""IEEE 1149.1 TAP state reference aligned with jtag_driver_enhanced."""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, Tuple


class TAPState(IntEnum):
    TEST_LOGIC_RESET = 0
    RUN_TEST_IDLE = 1
    SELECT_DR_SCAN = 2
    CAPTURE_DR = 3
    SHIFT_DR = 4
    EXIT1_DR = 5
    PAUSE_DR = 6
    EXIT2_DR = 7
    UPDATE_DR = 8
    SELECT_IR_SCAN = 9
    CAPTURE_IR = 10
    SHIFT_IR = 11
    EXIT1_IR = 12
    PAUSE_IR = 13
    EXIT2_IR = 14
    UPDATE_IR = 15
    TAP_UNKNOWN = 16


def next_tap_state(current: TAPState, tms: int) -> TAPState:
    t = 1 if tms else 0
    if current == TAPState.TAP_UNKNOWN:
        return TAPState.TEST_LOGIC_RESET
    if current == TAPState.TEST_LOGIC_RESET:
        return TAPState.TEST_LOGIC_RESET if t else TAPState.RUN_TEST_IDLE
    if current == TAPState.RUN_TEST_IDLE:
        return TAPState.SELECT_DR_SCAN if t else TAPState.RUN_TEST_IDLE
    if current == TAPState.SELECT_DR_SCAN:
        return TAPState.SELECT_IR_SCAN if t else TAPState.CAPTURE_DR
    if current == TAPState.CAPTURE_DR:
        return TAPState.EXIT1_DR if t else TAPState.SHIFT_DR
    if current == TAPState.SHIFT_DR:
        return TAPState.EXIT1_DR if t else TAPState.SHIFT_DR
    if current == TAPState.EXIT1_DR:
        return TAPState.UPDATE_DR if t else TAPState.PAUSE_DR
    if current == TAPState.PAUSE_DR:
        return TAPState.EXIT2_DR if t else TAPState.PAUSE_DR
    if current == TAPState.EXIT2_DR:
        return TAPState.UPDATE_DR if t else TAPState.SHIFT_DR
    if current == TAPState.UPDATE_DR:
        return TAPState.SELECT_DR_SCAN if t else TAPState.RUN_TEST_IDLE
    if current == TAPState.SELECT_IR_SCAN:
        return TAPState.TEST_LOGIC_RESET if t else TAPState.CAPTURE_IR
    if current == TAPState.CAPTURE_IR:
        return TAPState.EXIT1_IR if t else TAPState.SHIFT_IR
    if current == TAPState.SHIFT_IR:
        return TAPState.EXIT1_IR if t else TAPState.SHIFT_IR
    if current == TAPState.EXIT1_IR:
        return TAPState.UPDATE_IR if t else TAPState.PAUSE_IR
    if current == TAPState.PAUSE_IR:
        return TAPState.EXIT2_IR if t else TAPState.PAUSE_IR
    if current == TAPState.EXIT2_IR:
        return TAPState.UPDATE_IR if t else TAPState.SHIFT_IR
    if current == TAPState.UPDATE_IR:
        return TAPState.SELECT_DR_SCAN if t else TAPState.RUN_TEST_IDLE
    return TAPState.TEST_LOGIC_RESET


def all_legal_edges() -> Dict[Tuple[TAPState, int], TAPState]:
    out: Dict[Tuple[TAPState, int], TAPState] = {}
    for s in TAPState:
        if s == TAPState.TAP_UNKNOWN:
            continue
        for tm in (0, 1):
            out[(s, tm)] = next_tap_state(s, tm)
    return out
