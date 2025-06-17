# 📈 Kalman Pairs Trading Strategy

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![QuantConnect](https://img.shields.io/badge/platform-QuantConnect-black)](https://www.quantconnect.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

This project implements a robust statistical arbitrage strategy for trading mean-reverting pairs. It combines the **Engle-Granger cointegration test** with a **Kalman filter** to dynamically track the spread between two sector ETFs and execute trades based on statistically significant deviations.

---

## 📊 Strategy Overview

- **Backtest Period**: Jan 1, 2019 – Jan 1, 2023  
- **Capital**: $1,000,000  
- **Assets**: `XLK` (Tech), `XLU` (Utilities)  
- **Resolution**: Minute  
- **Approach**: Cointegration-based mean reversion  
- **Signal Smoothing**: Kalman filter  
- **Execution**: QuantConnect Lean Framework

---

## ⚙️ How It Works

### ✅ Recalibration (Weekly)
- Performs an **Engle-Granger cointegration test**.
- If cointegrated, computes the spread and cointegrating vector.
- Trains a **Kalman Filter** on recent spread data.
- Estimates a trading threshold using a **smoothed empirical survival function**.

### 📈 Daily Signal Evaluation
- Updates spread using the most recent prices.
- Applies Kalman filter to update the mean estimate.
- Checks whether the normalized spread crosses the threshold:
  - If below `-threshold`: **Go long spread**.
  - If above `+threshold`: **Go short spread**.
  - If reverting: **Exit position**.

---

## 📁 Repository Structure

```
.
├── PCADemo.py         # Core algorithm code (QuantConnect-style)
├── README.md          # This file
├── LICENSE            # MIT License
```

---

## 🚀 Getting Started

### 🔧 Prerequisites

To run this locally with [QuantConnect Lean CLI](https://github.com/QuantConnect/Lean):

```bash
# Clone this repository
git clone https://github.com/nilesh-mukherji/pair_trader.git
cd pair_trader

# Install Lean CLI if not already installed
pip install lean

# Run the backtest (you must have a QuantConnect account configured)
lean backtest "KalmanTrader"
```

Alternatively, run the code directly in QuantConnect's cloud environment by copying the contents of `PCADemo.py`.

---

## 🧠 Key Concepts

- **Cointegration**: Statistical relationship between two non-stationary time series that form a stationary linear combination.
- **Kalman Filter**: A recursive filter to estimate the dynamic mean of the spread.
- **Empirical Thresholding**: Uses a smoothed empirical function to identify significant deviations in spread.

---

## 📉 Performance

The strategy is designed to perform best during range-bound markets where the relationship between the selected ETFs remains stable. Performance results will vary depending on parameter choices and asset selection.

---

## 🔬 Future Enhancements

- Add **PCA-based ETF universe reduction**
- Adaptive **regime detection** for threshold scaling
- Robust **risk management** (volatility scaling, stop-losses)
- Integrate **optimization frameworks** for cointegration weights

---

## 🤝 Contributing

Pull requests are welcome! If you'd like to contribute:
1. Fork this repo.
2. Create your feature branch (`git checkout -b feature/foo`).
3. Commit your changes.
4. Push to the branch (`git push origin feature/foo`).
5. Open a pull request.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 📬 Contact

If you have questions, ideas, or feedback, feel free to open an issue or reach out via GitHub.
