"""Interactive visualization using Plotly"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any


def plot_equity_curve(
    results: Dict[str, Any],
    df: Optional[pd.DataFrame] = None,
    name: str = "Strategy",
    buy_hold_results: Optional[Dict[str, Any]] = None,
    save_path: Optional[str] = None,
    include_buy_hold: bool = False,
) -> go.Figure:
    """Plot equity curve with dates, benchmark, and trade markers

    Args:
        results: Backtest results dictionary
        df: OHLCV DataFrame with prices and datetime index
        name: Strategy name
        buy_hold_results: Buy & hold results for benchmark comparison
        save_path: Path to save plot (optional)
        include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

    Returns:
        Plotly figure object
    """
    equity_curve = results.get("equity_curve", [])

    if not equity_curve:
        print("No equity curve data available")
        return None

    fig = go.Figure()

    # Create x-axis (dates)
    if df is not None and len(df) == len(equity_curve):
        x_axis = df.index
    else:
        x_axis = list(range(len(equity_curve)))

    # Add strategy equity curve
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=equity_curve,
            name=f"{name} Equity",
            line=dict(color="#26a69a", width=2),
            hovertemplate="<b>%{x}</b><br>Equity: $%{y:,.2f}<extra></extra>",
        )
    )

    # Add buy & hold benchmark (always include if data available, control visibility)
    if buy_hold_results:
        initial_capital_bah = buy_hold_results.get("initial_capital", 10000)
        start_price = buy_hold_results.get("start_price")
        end_price = buy_hold_results.get("end_price")

        if (
            df is not None
            and start_price
            and end_price
            and len(df) == len(equity_curve)
        ):
            # Calculate buy & hold equity curve
            bah_equity = [
                initial_capital_bah * (price / start_price)
                for price in df["close"].values
            ]
            fig.add_trace(
                go.Scatter(
                    x=x_axis,
                    y=bah_equity,
                    name="Buy & Hold",
                    line=dict(color="gray", width=2, dash="dash"),
                    hovertemplate="<b>%{x}</b><br>Buy & Hold: $%{y:,.2f}<extra></extra>",
                    visible=include_buy_hold,
                )
            )

    # Add initial capital line
    initial_capital = results.get("initial_capital", 10000)
    fig.add_hline(
        y=initial_capital,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Initial Capital",
        annotation_position="right",
    )

    # Add annotations for peak and final equity
    final_equity = equity_curve[-1]
    peak_equity = max(equity_curve)
    peak_index = equity_curve.index(peak_equity)

    fig.add_annotation(
        x=x_axis[peak_index] if isinstance(x_axis, (list, pd.Index)) else peak_index,
        y=peak_equity,
        text=f"Peak: ${peak_equity:,.2f}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#26a69a",
        ax=0,
        ay=-40,
        bgcolor="rgba(255,255,255,0.8)",
    )

    fig.add_annotation(
        x=x_axis[-1] if isinstance(x_axis, (list, pd.Index)) else len(equity_curve) - 1,
        y=final_equity,
        text=f"Final: ${final_equity:,.2f}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#26a69a",
        ax=-40,
        ay=0,
        bgcolor="rgba(255,255,255,0.8)",
    )

    fig.update_layout(
        title=f"{name} - Equity Curve",
        xaxis_title="Date" if df is not None else "Bar",
        yaxis_title="Equity ($)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
        xaxis_rangeslider_visible=True,
    )

    if save_path:
        has_bah = bool(buy_hold_results and df is not None)
        if has_bah:
            html = fig.to_html(include_plotlyjs="cdn", full_html=True)
            toggle_script = """
    <script>
        // Check URL parameter for bah visibility
        function checkBahParameter() {
            const params = new URLSearchParams(window.location.search);
            const showBah = params.get('bah') === '1';
            
            // Find\` div id dynamically (it changes each time)
            const plotDiv = document.querySelector('.plotly-graph-div');
            if (plotDiv) {
                Plotly.restyle(plotDiv, {
                    visible: [true, showBah]
                });
            }
        }
        
        // Check on page load
        checkBahParameter();
    </script>
"""
            html = html.replace("</body>", toggle_script + "</body>")
            with open(save_path, "w") as f:
                f.write(html)
        else:
            fig.write_html(save_path)
        print(f"Saved equity curve to {save_path}")

    return fig


def plot_drawdown(
    results: Dict[str, Any],
    df: Optional[pd.DataFrame] = None,
    name: str = "Strategy",
    save_path: Optional[str] = None,
    buy_hold_results: Optional[Dict[str, Any]] = None,
    include_buy_hold: bool = False,
) -> go.Figure:
    """Plot drawdown chart with dates and recovery periods

    Args:
        results: Backtest results dictionary
        df: OHLCV DataFrame with datetime index
        name: Strategy name
        save_path: Path to save plot (optional)
        buy_hold_results: Buy & hold results for benchmark comparison
        include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

    Returns:
        Plotly figure object
    """
    equity_curve = results.get("equity_curve", [])

    if not equity_curve:
        print("No equity curve data available")
        return None

    # Create x-axis (dates)
    if df is not None and len(df) == len(equity_curve):
        x_axis = df.index
    else:
        x_axis = list(range(len(equity_curve)))

    # Calculate drawdown
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100

    fig = go.Figure()

    # Add drawdown area
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=drawdown,
            fill="tozeroy",
            name="Drawdown",
            line=dict(color="#ef5350", width=1),
            fillcolor="rgba(239, 83, 80, 0.3)",
            hovertemplate="<b>%{x}</b><br>Drawdown: %{y:.2f}%<extra></extra>",
            visible=True,
        )
    )

    # Add BaH drawdown if requested
    if buy_hold_results and df is not None:
        initial_capital_bah = buy_hold_results.get("initial_capital", 10000)
        start_price = buy_hold_results.get("start_price")
        end_price = buy_hold_results.get("end_price")

        if start_price and end_price and len(df) == len(equity_curve):
            # Calculate buy & hold equity curve
            bah_equity = [
                initial_capital_bah * (price / start_price)
                for price in df["close"].values
            ]
            bah_equity_array = np.array(bah_equity)
            bah_running_max = np.maximum.accumulate(bah_equity_array)
            bah_drawdown = (bah_equity_array - bah_running_max) / bah_running_max * 100

            fig.add_trace(
                go.Scatter(
                    x=x_axis,
                    y=bah_drawdown,
                    fill="tozeroy",
                    name="Buy & Hold Drawdown",
                    line=dict(color="gray", width=1, dash="dash"),
                    fillcolor="rgba(128, 128, 128, 0.2)",
                    hovertemplate="<b>%{x}</b><br>BaH Drawdown: %{y:.2f}%<extra></extra>",
                    visible=include_buy_hold,
                )
            )

    # Add max drawdown annotation (strategy)
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]

    fig.add_annotation(
        x=x_axis[max_dd_idx] if isinstance(x_axis, (list, pd.Index)) else max_dd_idx,
        y=max_dd,
        text=f"Max Drawdown: {max_dd:.2f}%",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#ef5350",
        ax=0,
        ay=40,
        bgcolor="rgba(255,255,255,0.8)",
        font=dict(color="#ef5350", size=12),
    )

    fig.update_layout(
        title=f"{name} - Drawdown Chart",
        xaxis_title="Date" if df is not None else "Bar",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        showlegend=False,
    )

    if save_path:
        has_bah = bool(buy_hold_results and df is not None)

        if has_bah:
            toggle_script = """
    <script>
        // Check URL parameter for bah visibility
        function checkBahParameter() {
            const params = new URLSearchParams(window.location.search);
            const showBah = params.get('bah') === '1';

            // Find div id dynamically (it changes each time)
            const plotDiv = document.querySelector('.plotly-graph-div');
            if (plotDiv) {
                Plotly.restyle(plotDiv, {
                    visible: [true, showBah]
                });
            }
        }

        // Check on page load
        checkBahParameter();
    </script>
"""
            html = fig.to_html()
            html = html.replace("</body>", toggle_script + "</body>")
            with open(save_path, "w") as f:
                f.write(html)
        else:
            fig.write_html(save_path)
        print(f"Saved drawdown chart to {save_path}")

    return fig


def plot_monthly_returns(
    results: Dict[str, Any],
    timestamps: pd.Index,
    name: str = "Strategy",
    save_path: Optional[str] = None,
    use_bar_chart: bool = True,
    df: Optional[pd.DataFrame] = None,
    buy_hold_results: Optional[Dict[str, Any]] = None,
    include_buy_hold: bool = False,
) -> go.Figure:
    """Plot monthly returns as bar chart (or heatmap)

    Args:
        results: Backtest results dictionary
        timestamps: Timestamp index
        name: Strategy name
        save_path: Path to save plot (optional)
        use_bar_chart: If True, use bar chart; if False, use heatmap
        buy_hold_results: Buy & hold results for benchmark comparison
        include_buy_hold: Whether to include Buy & Hold benchmark (default: False)

    Returns:
        Plotly figure object
    """
    equity_curve = results.get("equity_curve", [])

    if not equity_curve or len(timestamps) == 0:
        print("No data available for monthly returns")
        return None

    # Create DataFrame and resample monthly
    equity_df = pd.DataFrame({"equity": equity_curve}, index=timestamps)
    monthly = equity_df.resample("ME").last().dropna()

    if len(monthly) < 2:
        print("Not enough data for monthly returns")
        return None

    # Calculate monthly returns
    monthly_returns = monthly.pct_change().dropna() * 100

    fig = go.Figure()

    if use_bar_chart:
        # Bar chart version
        monthly_returns = monthly_returns.reset_index()
        monthly_returns["year_month"] = monthly_returns["timestamp"].dt.strftime(
            "%Y-%m"
        )

        colors = ["#26a69a" if r >= 0 else "#ef5350" for r in monthly_returns["equity"]]

        fig.add_trace(
            go.Bar(
                x=monthly_returns["year_month"],
                y=monthly_returns["equity"],
                name="Strategy",
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>Strategy: %{y:.2f}%<extra></extra>",
            )
        )

        # Add buy & hold benchmark (always include if data available, control visibility)
        if buy_hold_results and df is not None:
            initial_capital_bh = buy_hold_results.get("initial_capital", 10000)
            start_price = buy_hold_results.get("start_price")
            end_price = buy_hold_results.get("end_price")

            if start_price and end_price and len(df) == len(timestamps):
                # Calculate buy & hold equity curve
                bah_equity = [
                    initial_capital_bh * (price / start_price)
                    for price in df["close"].values
                ]
                df_bh = pd.DataFrame({"equity": bah_equity}, index=timestamps)
                monthly_bh = df_bh.resample("ME").last().dropna()
                monthly_bh_returns = monthly_bh.pct_change().dropna() * 100

                if len(monthly_bh_returns) > 0 and len(monthly_bh_returns) == len(
                    monthly_returns
                ):
                    monthly_bh_returns = monthly_bh_returns.reset_index()
                    monthly_bh_returns["year_month"] = monthly_bh_returns[
                        "timestamp"
                    ].dt.strftime("%Y-%m")

                    fig.add_trace(
                        go.Bar(
                            x=monthly_bh_returns["year_month"],
                            y=monthly_bh_returns["equity"],
                            name="Buy & Hold",
                            marker_color="rgba(100, 100, 100, 0.3)",
                            hovertemplate="<b>%{x}</b><br>Buy & Hold: %{y:.2f}%<extra></extra>",
                            visible=include_buy_hold,
                        )
                    )

        fig.update_layout(
            title=f"{name} - Monthly Returns (%)",
            xaxis_title="Month",
            yaxis_title="Return (%)",
            template="plotly_white",
            height=500,
            showlegend=include_buy_hold,
        )
    else:
        # Heatmap version (original)
        monthly_returns = monthly_returns.reset_index()
        monthly_returns["year"] = monthly_returns["timestamp"].dt.year
        monthly_returns["month"] = monthly_returns["timestamp"].dt.month_name()

        # Pivot for heatmap
        heatmap_data = monthly_returns.pivot(
            index="month", columns="year", values="equity"
        )

        month_order = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        heatmap_data = heatmap_data.reindex(month_order)

        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale="RdYlGn",
                text=heatmap_data.values.round(1),
                texttemplate="%{text}%",
                textfont={"size": 10},
                hoverongaps=False,
                hoverinfo="text+z",
            )
        )

        fig.update_layout(
            title=f"{name} - Monthly Returns (%)",
            xaxis_title="Year",
            yaxis_title="Month",
            template="plotly_white",
            height=600,
        )

    if save_path:
        has_bah = bool(buy_hold_results and df is not None)
        if has_bah:
            html = fig.to_html(include_plotlyjs="cdn", full_html=True)
            toggle_script = """
    <script>
        // Check URL parameter for bah visibility
        function checkBahParameter() {
            const params = new URLSearchParams(window.location.search);
            const showBah = params.get('bah') === '1';
            
            // Find\` div id dynamically (it changes each time)
            const plotDiv = document.querySelector('.plotly-graph-div');
            if (plotDiv) {
                Plotly.restyle(plotDiv, {
                    visible: [true, showBah]
                });
            }
        }
        
        // Check on page load
        checkBahParameter();
    </script>
"""
            html = html.replace("</body>", toggle_script + "</body>")
            with open(save_path, "w") as f:
                f.write(html)
        else:
            fig.write_html(save_path)
        print(f"Saved monthly returns to {save_path}")

    return fig


def plot_pnl_distribution(
    results: Dict[str, Any],
    name: str = "Strategy",
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot PnL distribution histogram with color-coded bars

    Args:
        results: Backtest results dictionary
        name: Strategy name
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    trades = results.get("trades", [])

    if not trades:
        print("No trades available")
        return None

    pnls = [t["pnl"] for t in trades]
    colors = ["#26a69a" if pnl >= 0 else "#ef5350" for pnl in pnls]

    fig = go.Figure()

    # Add histogram
    fig.add_trace(
        go.Histogram(
            x=pnls,
            nbinsx=50,
            name="PnL Distribution",
            marker_color=colors,
            hovertemplate="<b>Range</b><br>PnL: $%{x:.2f}<br>Count: %{y}<extra></extra>",
        )
    )

    # Add zero line
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.7)

    # Add stats lines
    avg_pnl = np.mean(pnls)
    median_pnl = np.median(pnls)

    fig.add_vline(
        x=avg_pnl,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"Avg: ${avg_pnl:.2f}",
        annotation_position="top left",
    )

    fig.add_vline(
        x=median_pnl,
        line_dash="dot",
        line_color="purple",
        annotation_text=f"Median: ${median_pnl:.2f}",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"{name} - PnL Distribution",
        xaxis_title="PnL ($)",
        yaxis_title="Frequency",
        template="plotly_white",
        height=500,
        showlegend=False,
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved PnL distribution to {save_path}")

    return fig


def plot_trade_performance_timeline(
    results: Dict[str, Any],
    name: str = "Strategy",
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot trade performance timeline (Chart C)
    Scatter plot showing PnL over time with rolling average

    Args:
        results: Backtest results dictionary
        name: Strategy name
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    trades = results.get("trades", [])

    if not trades:
        print("No trades available")
        return None

    # Filter trades with entry_time
    trades_with_time = [t for t in trades if t.get("entry_time") is not None]

    if not trades_with_time:
        print("No trades with timestamps available")
        return None

    entry_times = [t["entry_time"] for t in trades_with_time]
    pnls = [t["pnl"] for t in trades_with_time]

    # Calculate trade duration
    durations = []
    for t in trades_with_time:
        if t.get("exit_time") is not None and t.get("entry_time") is not None:
            duration = (
                t["exit_time"] - t["entry_time"]
            ).total_seconds() / 3600  # hours
            durations.append(duration)
        else:
            durations.append(1)

    # Colors based on PnL
    colors = ["#26a69a" if pnl >= 0 else "#ef5350" for pnl in pnls]
    sizes = [max(10, min(30, duration * 2)) for duration in durations]

    fig = go.Figure()

    # Add scatter plot for trades
    fig.add_trace(
        go.Scatter(
            x=entry_times,
            y=pnls,
            mode="markers",
            name="Trades",
            marker=dict(color=colors, size=sizes, opacity=0.7),
            text=[
                f"PnL: ${pnl:.2f}<br>Duration: {dur:.1f}h<br>Reason: {t['reason']}"
                for pnl, dur, t in zip(pnls, durations, trades_with_time)
            ],
            hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)

    # Calculate cumulative PnL for trend
    cumulative_pnl = np.cumsum(pnls)

    # Add cumulative PnL as secondary line
    fig.add_trace(
        go.Scatter(
            x=entry_times,
            y=cumulative_pnl,
            name="Cumulative PnL",
            line=dict(color="#26a69a", width=2),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Cumulative: $%{y:,.2f}<extra></extra>",
        )
    )

    # Add annotations
    max_cumulative = max(cumulative_pnl)
    max_cum_idx = np.argmax(cumulative_pnl)
    min_cumulative = min(cumulative_pnl)
    min_cum_idx = np.argmin(cumulative_pnl)

    fig.add_annotation(
        x=entry_times[max_cum_idx],
        y=max_cumulative,
        text=f"Peak: ${max_cumulative:,.2f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#26a69a",
        ax=0,
        ay=-40,
        bgcolor="rgba(255,255,255,0.8)",
        yref="y2",
    )

    fig.add_annotation(
        x=entry_times[min_cum_idx],
        y=min_cumulative,
        text=f"Low: ${min_cumulative:,.2f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#ef5350",
        ax=0,
        ay=40,
        bgcolor="rgba(255,255,255,0.8)",
        yref="y2",
    )

    fig.update_layout(
        title=f"{name} - Trade Performance Timeline",
        xaxis_title="Date",
        yaxis_title="Trade PnL ($)",
        yaxis2=dict(
            title="Cumulative PnL ($)",
            overlaying="y",
            side="right",
        ),
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved trade performance timeline to {save_path}")

    return fig


def plot_win_rate_over_time(
    results: Dict[str, Any],
    name: str = "Strategy",
    window: int = 20,
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot win rate over time (Chart D)
    Rolling window win rate with overall win rate

    Args:
        results: Backtest results dictionary
        name: Strategy name
        window: Rolling window size for win rate calculation
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    trades = results.get("trades", [])

    if not trades:
        print("No trades available")
        return None

    # Filter trades with entry_time
    trades_with_time = [t for t in trades if t.get("entry_time") is not None]

    if not trades_with_time:
        print("No trades with timestamps available")
        return None

    entry_times = [t["entry_time"] for t in trades_with_time]
    wins = [1 if t["pnl"] > 0 else 0 for t in trades_with_time]

    # Calculate rolling win rate
    rolling_win_rate = (
        pd.Series(wins).rolling(window=window, min_periods=1).mean() * 100
    )

    # Calculate cumulative win rate
    cumulative_win_rate = [np.mean(wins[: i + 1]) * 100 for i in range(len(wins))]
    overall_win_rate = cumulative_win_rate[-1]

    fig = go.Figure()

    # Add rolling win rate
    fig.add_trace(
        go.Scatter(
            x=entry_times,
            y=rolling_win_rate,
            name=f"Rolling Win Rate ({window} trades)",
            line=dict(color="#26a69a", width=2),
            hovertemplate="<b>%{x}</b><br>Rolling: %{y:.1f}%<extra></extra>",
        )
    )

    # Add cumulative win rate
    fig.add_trace(
        go.Scatter(
            x=entry_times,
            y=cumulative_win_rate,
            name="Cumulative Win Rate",
            line=dict(color="gray", width=2, dash="dash"),
            hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>",
        )
    )

    # Add overall win rate line
    fig.add_hline(
        y=overall_win_rate,
        line_dash="dot",
        line_color="purple",
        annotation_text=f"Overall: {overall_win_rate:.1f}%",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"{name} - Win Rate Over Time",
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        yaxis_range=[0, 100],
        hovermode="x unified",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved win rate over time to {save_path}")

    return fig


def plot_trade_duration_distribution(
    results: Dict[str, Any],
    name: str = "Strategy",
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot trade duration distribution histogram

    Args:
        results: Backtest results dictionary
        name: Strategy name
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    trades = results.get("trades", [])

    if not trades:
        print("No trades available")
        return None

    # Calculate durations in hours
    durations = []
    for t in trades:
        if t.get("exit_time") is not None and t.get("entry_time") is not None:
            duration = (
                t["exit_time"] - t["entry_time"]
            ).total_seconds() / 3600  # hours
            durations.append(duration)

    if not durations:
        print("No trade duration data available")
        return None

    colors = [
        "#26a69a" if t["pnl"] >= 0 else "#ef5350"
        for t in trades
        if t.get("entry_time") is not None and t.get("exit_time") is not None
    ]

    fig = go.Figure()

    # Add histogram
    fig.add_trace(
        go.Histogram(
            x=durations,
            nbinsx=30,
            name="Trade Duration",
            marker_color=colors,
            hovertemplate="<b>Range</b><br>Duration: %{x:.1f}h<br>Count: %{y}<extra></extra>",
        )
    )

    # Add stats
    avg_duration = np.mean(durations)
    median_duration = np.median(durations)

    fig.add_vline(
        x=avg_duration,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"Avg: {avg_duration:.1f}h",
        annotation_position="top left",
    )

    fig.add_vline(
        x=median_duration,
        line_dash="dot",
        line_color="purple",
        annotation_text=f"Median: {median_duration:.1f}h",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"{name} - Trade Duration Distribution",
        xaxis_title="Duration (hours)",
        yaxis_title="Frequency",
        template="plotly_white",
        height=500,
        showlegend=False,
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved trade duration distribution to {save_path}")

    return fig


def plot_position_size_over_time(
    results: Dict[str, Any],
    name: str = "Strategy",
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot position size over time

    Args:
        results: Backtest results dictionary
        name: Strategy name
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    trades = results.get("trades", [])

    if not trades:
        print("No trades available")
        return None

    # Filter trades with entry_time
    trades_with_time = [t for t in trades if t.get("entry_time") is not None]

    if not trades_with_time:
        print("No trades with timestamps available")
        return None

    # Calculate position sizes
    entry_times = [t["entry_time"] for t in trades_with_time]
    position_sizes = []
    for t in trades_with_time:
        if t["entry"] > 0:
            size = (
                t["pnl"] / (t["exit"] - t["entry"]) * t["entry"]
                if t["exit"] != t["entry"]
                else 0
            )
            position_sizes.append(abs(size))
        else:
            position_sizes.append(0)

    colors = ["#26a69a" if t["pnl"] >= 0 else "#ef5350" for t in trades_with_time]

    fig = go.Figure()

    # Add scatter plot
    fig.add_trace(
        go.Scatter(
            x=entry_times,
            y=position_sizes,
            mode="markers+lines",
            name="Position Size",
            marker=dict(color=colors, size=8),
            line=dict(color="gray", width=1),
            hovertemplate="<b>%{x}</b><br>Size: $%{y:,.2f}<br>PnL: $%{text:.2f}<extra></extra>",
            text=[t["pnl"] for t in trades_with_time],
        )
    )

    fig.update_layout(
        title=f"{name} - Position Size Over Time",
        xaxis_title="Date",
        yaxis_title="Position Size ($)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        showlegend=False,
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved position size over time to {save_path}")

    return fig


def plot_equity_comparison(
    results_dict: Dict[str, Dict[str, Any]],
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot multiple equity curves for comparison

    Args:
        results_dict: Dictionary of {name: results}
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    if not results_dict:
        print("No results to compare")
        return None

    fig = go.Figure()

    colors = px.colors.qualitative.Plotly

    for i, (name, results) in enumerate(results_dict.items()):
        equity_curve = results.get("equity_curve", [])

        if equity_curve:
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    y=equity_curve,
                    name=name,
                    line=dict(color=color, width=2),
                    hovertemplate="<b>Bar: %{x}</b><br>Equity: $%{y:,.2f}<extra></extra>",
                )
            )

    fig.update_layout(
        title="Equity Curve Comparison",
        xaxis_title="Bar",
        yaxis_title="Equity ($)",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved equity comparison to {save_path}")

    return fig


def plot_radar_chart(
    results_dict: Dict[str, Dict[str, Any]],
    metrics: List[str],
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot radar chart for multi-metric comparison

    Args:
        results_dict: Dictionary of {name: results}
        metrics: List of metric names to compare
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    if not results_dict or not metrics:
        print("No data for radar chart")
        return None

    # Normalize metrics to 0-1 range
    fig = go.Figure()

    # Get metric values for each strategy
    all_values = []
    for results in results_dict.values():
        values = []
        for metric in metrics:
            value = results.get(metric, 0)
            values.append(value)
        all_values.append(values)

    # Find max/min for normalization
    all_values_flat = [v for sublist in all_values for v in sublist]
    max_val = max(all_values_flat) if all_values_flat else 1
    min_val = min(all_values_flat) if all_values_flat else 0

    # Add traces
    for i, (name, results) in enumerate(results_dict.items()):
        values = []
        for metric in metrics:
            value = results.get(metric, 0)
            # Normalize to 0-1
            normalized = (
                (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            )
            values.append(normalized)

        fig.add_trace(
            go.Scatterpolar(r=values, theta=metrics, name=name, fill="toself")
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Strategy Comparison - Normalized Metrics",
        template="plotly_white",
        height=600,
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved radar chart to {save_path}")

    return fig


def plot_metrics_comparison(
    results_dict: Dict[str, Dict[str, Any]],
    metrics: List[str],
    save_path: Optional[str] = None,
) -> go.Figure:
    """Plot bar chart for metrics comparison

    Args:
        results_dict: Dictionary of {name: results}
        metrics: List of metric names to compare
        save_path: Path to save plot (optional)

    Returns:
        Plotly figure object
    """
    if not results_dict or not metrics:
        print("No data for metrics comparison")
        return None

    fig = go.Figure()

    for i, metric in enumerate(metrics):
        values = []
        names = []

        for name, results in results_dict.items():
            names.append(name)
            values.append(results.get(metric, 0))

        fig.add_trace(
            go.Bar(
                x=names,
                y=values,
                name=metric,
                marker_color=px.colors.qualitative.Plotly[i],
            )
        )

    fig.update_layout(
        title="Metrics Comparison",
        yaxis_title="Value",
        template="plotly_white",
        height=600,
        barmode="group",
    )

    if save_path:
        fig.write_html(save_path)
        print(f"Saved metrics comparison to {save_path}")

    return fig
