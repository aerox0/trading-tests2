//@version=6
strategy("EMA100 Trading Strategy", overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=10)

// Input parameters
emaPeriod = input.int(100, "EMA Period", minval=1)
stopLossPct = input.float(2.0, "Stop Loss %", minval=0.1, maxval=50) / 100
takeProfitPct = input.float(4.0, "Take Profit %", minval=0.1, maxval=50) / 100
cooldownMinutes = input.int(30, "Cooldown Period (minutes)", minval=1)

// Calculate EMA
ema100 = ta.ema(close, emaPeriod)

// Plot EMA
plot(ema100, color=color.blue, linewidth=2, title="EMA100")

// Track cooldown state
var float lastExitTime = na
var bool canTrade = true

// Check if cooldown is over
if not na(lastExitTime)
    if time >= lastExitTime + (cooldownMinutes * 60 * 1000)
        canTrade := true
        lastExitTime := na

// Entry condition: price above EMA100, no position, cooldown over
longCondition = close > ema100 and strategy.position_size == 0 and canTrade

// Entry
if longCondition
    strategy.entry("Long", strategy.long)
    canTrade := false

// Exit conditions - only when position exists
if strategy.position_size > 0
    stopLossPrice = strategy.position_avg_price * (1 - stopLossPct)
    takeProfitPrice = strategy.position_avg_price * (1 + takeProfitPct)
    
    strategy.exit("Exit", "Long", stop=stopLossPrice, limit=takeProfitPrice)

// Set cooldown when position closes
if strategy.position_size == 0 and strategy.position_size[1] != 0
    lastExitTime := time

// Plot entry signals
plotshape(longCondition, title="Buy Signal", location=location.belowbar, color=color.green, style=shape.labelup, text="BUY")
