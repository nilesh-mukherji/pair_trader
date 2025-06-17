import numpy as np
from AlgorithmImports import *
from arch.unitroot.cointegration import engle_granger
from pykalman import KalmanFilter
import pandas as pd

class KalmanTrader(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2023, 1, 1)

        self.set_cash(1000000)
        self.set_benchmark(self.add_equity("SPY").symbol)
        self.assets = ["XLK", "XLU"]
        
        for asset in self.assets:
            self.add_equity(asset, Resolution.MINUTE)
        
        self.kalman_filter = None
        self.current_mean = None
        self.current_cov = None
        self.trading_weight = pd.Series()
        self.coint_vector = None
        self.state = 0
        
        self.recalibrate()
        self.schedule.on(self.date_rules.week_start(), self.time_rules.at(0, 0), self.recalibrate)
        self.schedule.on(self.date_rules.every_day(), self.time_rules.before_market_close(self.assets[0]), self.every_day_before_market_close)

    def recalibrate(self):
        history = self.history(self.assets, 252*2, Resolution.DAILY)
        if history.empty: return
        
        data = history['close'].unstack(level=0)
        log_price = np.log(data)
        
        coint_result = engle_granger(log_price.iloc[:, 0], log_price.iloc[:, 1], trend="ct", lags=0)
        if coint_result.pvalue > 0.4:
            self.debug("Cointegration test did not pass. Recalibration aborted. Liquidating positions.")
            self.liquidate()
            self.trading_weight = pd.Series()
            self.state = 0
            return
        
        self.coint_vector = coint_result.cointegrating_vector[:2]
        spread = log_price @ self.coint_vector
        
        self.kalman_filter = KalmanFilter(transition_matrices=[1], observation_matrices=[1],
                                          initial_state_mean=spread.iloc[:20].mean(),
                                          observation_covariance=spread.iloc[:20].var(),
                                          em_vars=['transition_covariance', 'initial_state_covariance'])
        self.kalman_filter = self.kalman_filter.em(spread.iloc[:20], n_iter=5)
        filtered_state_means, filtered_state_covariances = self.kalman_filter.filter(spread.iloc[:20])
        
        self.current_mean = filtered_state_means[-1, :]
        self.current_cov = filtered_state_covariances[-1, :]
        
        mean_series = np.array([None] * (spread.shape[0] - 20))
        for i in range(20, spread.shape[0]):
            self.current_mean, self.current_cov = self.kalman_filter.filter_update(filtered_state_mean=self.current_mean,
                                                                                   filtered_state_covariance=self.current_cov,
                                                                                   observation=spread.iloc[i])
            mean_series[i - 20] = float(self.current_mean)
        
        normalized_spread = spread.iloc[20:] - mean_series
        
        s0 = np.linspace(0, max(normalized_spread), 50)
        f_bar = np.array([len(normalized_spread[normalized_spread > s0[i]]) / normalized_spread.shape[0] for i in range(50)])
        D = np.zeros((49, 50))
        for i in range(49):
            D[i, i] = 1
            D[i, i + 1] = -1
        
        l = 1.0
        f_star = np.linalg.inv(np.eye(50) + l * D.T @ D) @ f_bar.reshape(-1, 1)
        s_star = [f_star[i] * s0[i] for i in range(50)]
        self.threshold = s0[np.argmax(s_star)]
        self.trading_weight = self.coint_vector / np.sum(np.abs(self.coint_vector))

    def every_day_before_market_close(self):
        qb = self
        if self.trading_weight.isnull().all():
            return
        
        log_series = pd.Series({symbol: np.log(qb.securities[symbol].close) for symbol in self.assets})
        
        # self.debug((f"Log Price: {log_series} | {log_series.shape}, Coint: {self.coint_vector} | {self.coint_vector.shape}"))
        
        spread = log_series.to_numpy() @ self.coint_vector.to_numpy()
        
        self.current_mean, self.current_cov = self.kalman_filter.filter_update(filtered_state_mean=self.current_mean,
                                                                               filtered_state_covariance=self.current_cov,
                                                                               observation=spread)
        normalized_spread = spread - self.current_mean
        
        if self.state == 0 and normalized_spread < -self.threshold:
            self.set_holdings([PortfolioTarget(self.assets[i], self.trading_weight[i]) for i in range(len(self.assets))])
            self.state = 1
        elif self.state == 0 and normalized_spread > self.threshold:
            self.set_holdings([PortfolioTarget(self.assets[i], -self.trading_weight[i]) for i in range(len(self.assets))])
            self.state = -1
        elif self.state == 1 and normalized_spread > -self.threshold or self.state == -1 and normalized_spread < self.threshold:
            self.liquidate()
            self.state = 0
