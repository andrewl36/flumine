import datetime
from typing import Tuple
from betfairlightweight.resources.bettingresources import MarketBook, RunnerBook

from .utils import SimulatedPlaceResponse
from ..utils import get_price
from ..order.ordertype import OrderTypes


class Simulated:
    """
    Class to hold `simulated` order
    matching and status.
    """

    def __init__(self, order):
        self.order = order
        self.matched = []

    def __call__(self, market_book: MarketBook, traded: dict):
        # simulates order matching
        runner = self._get_runner(market_book)
        if self.take_sp and market_book.bsp_reconciled:
            self._process_sp(runner)  # todo simulate limitOrder with `TAKE SP`

        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            self._process_traded(runner, traded)

    def place(
        self, market_book: MarketBook, instruction: dict, bet_id: int
    ) -> SimulatedPlaceResponse:
        # simulates placeOrder request->matching->response
        # todo instruction/fillkill/timeInForce/BPE etc
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            runner = self._get_runner(market_book)
            available_to_back = get_price(runner.ex.available_to_back, 0) or 1.01
            available_to_lay = get_price(runner.ex.available_to_lay, 0) or 1000
            price = self.order.order_type.price
            size = self.order.order_type.size
            if self.order.side == "BACK":
                # available = runner.ex.available_to_lay
                if available_to_back >= price:
                    self._process_price_matched(
                        price, size, runner.ex.available_to_back
                    )
            else:
                # available = runner.ex.available_to_back
                if available_to_lay <= price:
                    self._process_price_matched(price, size, runner.ex.available_to_lay)
            # todo on top
            return SimulatedPlaceResponse(
                status="SUCCESS",
                order_status="EXECUTABLE",
                bet_id=str(bet_id),
                average_price_matched=self.average_price_matched,
                size_matched=self.size_matched,
                placed_date=datetime.datetime.utcnow(),
                error_code=None,
            )
        else:
            raise NotImplementedError()  # todo

    def cancel(self):
        # simulates cancelOrder request->cancel->response
        pass

    def update(self):
        # simulates updateOrder request->update->response
        pass

    def replace(self):
        # simulates replaceOrder request->cancel/matching->response
        pass

    def _get_runner(self, market_book: MarketBook) -> RunnerBook:
        runner_dict = {
            (runner.selection_id, runner.handicap): runner
            for runner in market_book.runners
        }
        return runner_dict.get((self.order.selection_id, self.order.handicap))

    def _process_price_matched(
        self, price: float, size: float, available: list
    ) -> None:
        # calculate matched on execution
        size_remaining = size
        for avail in available:
            if size_remaining == 0:
                break
            elif (self.side == "BACK" and price <= avail.price) or (
                self.side == "LAY" and price >= avail.price
            ):
                _size_remaining = size_remaining
                size_remaining = max(size_remaining - avail.size, 0)
                if size_remaining == 0:
                    _size_matched = _size_remaining
                else:
                    _size_matched = avail.size
                _matched = (avail.price, _size_matched)
                self.matched.append(_matched)
            else:
                break

    def _process_sp(self, runner: RunnerBook) -> None:
        # calculate matched on BSP reconciliation
        actual_sp = runner.sp.actual_sp
        if actual_sp and self.size_remaining:
            _order_type = self.order.order_type
            if _order_type.ORDER_TYPE == OrderTypes.LIMIT:
                size = self.size_remaining
            elif _order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
                if self.side == "BACK":
                    if actual_sp < _order_type.price:
                        return
                    size = _order_type.liability
                else:
                    if actual_sp > _order_type.price:
                        return
                    size = round(_order_type.liability / (actual_sp - 1), 2)
            elif _order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
                if self.side == "BACK":
                    size = _order_type.liability
                else:
                    size = round(_order_type.liability / (actual_sp - 1), 2)
            else:
                raise NotImplementedError()
            self.matched.append((actual_sp, size))

    def _process_traded(self, runner: RunnerBook, traded: dict) -> None:
        # calculate matched on MarketBook update
        pass

    @staticmethod
    def _wap(matched: list) -> Tuple[float, float]:
        if not matched:
            return 0, 0
        a, b = 0, 0
        for match in matched:
            a += match[0] * match[1]
            b += match[1]
        if b == 0 or a == 0:
            return 0, 0
        else:
            return round(b, 2), round(a / b, 2)

    @property
    def take_sp(self) -> bool:
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            if self.order.order_type.persistence_type == "MARKET_ON_CLOSE":
                return True
            return False
        else:
            return True

    @property
    def side(self) -> str:
        return self.order.side

    @property
    def average_price_matched(self) -> float:
        if self.matched:
            _, avg_price_matched = self._wap(self.matched)
            return avg_price_matched
        else:
            return 0

    @property
    def size_matched(self) -> float:
        if self.matched:
            size_matched, _ = self._wap(self.matched)
            return size_matched
        else:
            return 0

    @property
    def size_remaining(self) -> float:
        return self.order.order_type.size - self.size_matched
