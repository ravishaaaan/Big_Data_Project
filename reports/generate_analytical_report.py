#!/usr/bin/env python3
"""
Modern Comprehensive Analytical Report Generator
Professional design with clean layouts and visual hierarchy
"""

import os
import sys
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_config import get_connection, query

# Modern minimalist color palette
COLORS = {
    'primary': '#2563eb',     # Blue 600
    'primary_light': '#dbeafe',  # Blue 100
    'success': '#059669',     # Emerald 600
    'success_light': '#d1fae5',  # Emerald 100
    'warning': '#d97706',     # Amber 600
    'warning_light': '#fef3c7',  # Amber 100
    'danger': '#dc2626',      # Red 600
    'danger_light': '#fee2e2',   # Red 100
    'dark': '#111827',        # Gray 900
    'medium': '#6b7280',      # Gray 500
    'light': '#f3f4f6',       # Gray 100
    'white': '#ffffff',
    'border': '#e5e7eb'       # Gray 200
}

# Clean modern style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.facecolor': COLORS['white'],
    'axes.facecolor': COLORS['white'],
    'axes.edgecolor': COLORS['border'],
    'axes.linewidth': 1.5,
    'grid.color': COLORS['border'],
    'grid.linestyle': '-',
    'grid.linewidth': 0.8,
    'grid.alpha': 0.4,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 10,
    'figure.titlesize': 16
})

OUTPUT_DIR = 'deliverables'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_comprehensive_statistics():
    """Get all statistics needed for comprehensive analysis"""
    conn = get_connection()
    stats = {}
    
    queries = {
        'transactions': """SELECT COUNT(*) as total_count, SUM(amount) as total_amount,
            AVG(amount) as avg_amount, MIN(amount) as min_amount, MAX(amount) as max_amount,
            COUNT(DISTINCT merchant_category) as category_count, COUNT(DISTINCT user_id) as unique_users
            FROM transactions""",
        'fraud_alerts': """SELECT COUNT(*) as total_fraud_alerts, COUNT(DISTINCT fraud_type) as fraud_type_count
            FROM fraud_alerts""",
        'fraud_by_type': """SELECT fraud_type, COUNT(*) as count FROM fraud_alerts
            GROUP BY fraud_type ORDER BY count DESC""",
        'fraud_impact': """SELECT f.fraud_type, COUNT(*) as count, COALESCE(SUM(t.amount), 0) as total_amount,
            COALESCE(AVG(t.amount), 0) as avg_amount, COALESCE(MAX(t.amount), 0) as max_amount
            FROM fraud_alerts f LEFT JOIN transactions t ON f.transaction_id = t.transaction_id
            GROUP BY f.fraud_type ORDER BY count DESC""",
        'fraud_by_merchant': """SELECT t.merchant_category, COUNT(*) as fraud_count,
            SUM(t.amount) as fraud_amount, AVG(t.amount) as avg_fraud_amount
            FROM fraud_alerts f JOIN transactions t ON f.transaction_id = t.transaction_id
            GROUP BY t.merchant_category ORDER BY fraud_count DESC""",
        'transactions_by_merchant': """SELECT merchant_category, COUNT(*) as tx_count,
            SUM(amount) as total_amount, AVG(amount) as avg_amount FROM transactions
            GROUP BY merchant_category ORDER BY tx_count DESC""",
        'validated': """SELECT COUNT(*) as validated_count, COALESCE(SUM(amount), 0) as validated_amount
            FROM validated_transactions""",
        'fraud_rate_by_category': """SELECT t.merchant_category, COUNT(*) as total_tx,
            COUNT(f.fraud_type) as fraud_tx, ROUND(100.0 * COUNT(f.fraud_type) / COUNT(*), 2) as fraud_rate_pct
            FROM transactions t LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
            GROUP BY t.merchant_category HAVING COUNT(f.fraud_type) > 0 ORDER BY fraud_rate_pct DESC""",
        'hourly_pattern': """SELECT EXTRACT(HOUR FROM event_time) as hour, COUNT(*) as tx_count,
            COUNT(f.fraud_type) as fraud_count FROM transactions t
            LEFT JOIN fraud_alerts f ON t.transaction_id = f.transaction_id
            GROUP BY EXTRACT(HOUR FROM event_time) ORDER BY hour""",
        'high_risk_users': """SELECT t.user_id, COUNT(DISTINCT f.transaction_id) as fraud_count,
            SUM(t.amount) as total_fraud_amount, COUNT(DISTINCT t.merchant_category) as categories_affected
            FROM fraud_alerts f JOIN transactions t ON f.transaction_id = t.transaction_id
            GROUP BY t.user_id HAVING COUNT(DISTINCT f.transaction_id) > 1 ORDER BY fraud_count DESC LIMIT 10"""
    }
    
    for key, sql in queries.items():
        result = query(conn, sql)
        stats[key] = result[0] if result and key in ['transactions', 'fraud_alerts', 'validated'] else (result if result else [])
    
    conn.close()
    return stats

def calculate_reconciliation_metrics(stats):
    """Calculate reconciliation and financial metrics"""
    tx = stats['transactions']
    fraud = stats['fraud_alerts']
    validated = stats['validated']
    
    metrics = {
        'total_transactions': tx.get('total_count', 0),
        'total_fraud_alerts': fraud.get('total_fraud_alerts', 0),
        'validated_count': validated.get('validated_count', 0),
        'total_amount': float(tx.get('total_amount', 0)),
        'validated_amount': float(validated.get('validated_amount', 0))
    }
    
    fraud_amount = sum(float(f.get('total_amount', 0)) for f in stats['fraud_impact'] if f['fraud_type'] == 'HIGH_VALUE')
    metrics['fraud_amount'] = fraud_amount
    metrics['expected_validated'] = metrics['total_transactions'] - metrics['total_fraud_alerts']
    metrics['validation_gap'] = metrics['expected_validated'] - metrics['validated_count']
    metrics['amount_reconciliation'] = metrics['total_amount'] - metrics['validated_amount'] - metrics['fraud_amount']
    metrics['fraud_rate'] = (metrics['total_fraud_alerts'] / metrics['total_transactions'] * 100) if metrics['total_transactions'] > 0 else 0
    
    return metrics

def add_page_header(fig, title, page_num=None):
    """Add clean modern page header"""
    # Header background
    header_ax = fig.add_axes([0, 0.93, 1, 0.07])
    header_ax.set_xlim(0, 1)
    header_ax.set_ylim(0, 1)
    header_ax.axis('off')
    
    # Add subtle top border
    header_ax.add_patch(Rectangle((0, 0.95), 1, 0.05, facecolor=COLORS['primary'], 
                                  transform=header_ax.transAxes, clip_on=False))
    
    # Title
    header_ax.text(0.03, 0.45, title, fontsize=18, fontweight='700', 
                   color=COLORS['dark'], va='center', transform=header_ax.transAxes)
    
    # Report name and date on right
    date_str = datetime.now(timezone.utc).strftime('%B %d, %Y')
    header_ax.text(0.97, 0.6, 'FRAUD DETECTION REPORT', fontsize=8, 
                   fontweight='600', color=COLORS['medium'], ha='right', 
                   va='center', transform=header_ax.transAxes)
    header_ax.text(0.97, 0.3, date_str, fontsize=8, 
                   color=COLORS['medium'], ha='right', va='center', 
                   transform=header_ax.transAxes)
    
    if page_num:
        header_ax.text(0.03, 0.05, f'Page {page_num}', fontsize=8, 
                      color=COLORS['medium'], va='center', transform=header_ax.transAxes)

def create_stat_card(ax, value, label, color, icon=None):
    """Create a clean metric card with large numbers"""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Card background with border
    card = Rectangle((0.02, 0.05), 0.96, 0.9, facecolor=COLORS['white'],
                     edgecolor=COLORS['border'], linewidth=2, 
                     transform=ax.transAxes, zorder=1)
    ax.add_patch(card)
    
    # Colored accent bar on left
    accent = Rectangle((0.02, 0.05), 0.015, 0.9, facecolor=color,
                       transform=ax.transAxes, zorder=2)
    ax.add_patch(accent)
    
    # Large value
    ax.text(0.5, 0.6, value, fontsize=28, fontweight='700', 
            color=COLORS['dark'], ha='center', va='center', 
            transform=ax.transAxes)
    
    # Label below
    ax.text(0.5, 0.3, label, fontsize=10, fontweight='500',
            color=COLORS['medium'], ha='center', va='center',
            transform=ax.transAxes)

def create_kpi_row(ax, label, value, change=None, is_good=None):
    """Create a KPI row with optional change indicator"""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Label
    ax.text(0.05, 0.5, label, fontsize=11, fontweight='500',
            color=COLORS['dark'], va='center', transform=ax.transAxes)
    
    # Value
    ax.text(0.95, 0.5, value, fontsize=13, fontweight='700',
            color=COLORS['dark'], ha='right', va='center', 
            transform=ax.transAxes)
    
    # Bottom border
    ax.plot([0.05, 0.95], [0.1, 0.1], color=COLORS['border'], 
            linewidth=1, transform=ax.transAxes)

def generate_comprehensive_pdf(output_path=None):
    """Generate modern organized PDF report"""
    if not output_path:
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(OUTPUT_DIR, f'7_comprehensive_analytical_report_{ts}.pdf')
    
    print(f"\n{'='*60}")
    print(f"GENERATING MODERN FRAUD DETECTION REPORT")
    print(f"{'='*60}")
    print(f"Output: {output_path}\n")
    
    stats = get_comprehensive_statistics()
    metrics = calculate_reconciliation_metrics(stats)
    
    with PdfPages(output_path) as pdf:
        # ============================================================
        # PAGE 1: EXECUTIVE SUMMARY
        # ============================================================
        fig = plt.figure(figsize=(11, 8.5))
        add_page_header(fig, 'Executive Summary', 1)
        
        # Main grid
        gs = fig.add_gridspec(5, 4, hspace=0.5, wspace=0.35, 
                             top=0.88, bottom=0.05, left=0.06, right=0.94)
        
        # Top row: 4 key metrics
        create_stat_card(fig.add_subplot(gs[0, 0]), 
                        f"{metrics['total_transactions']:,}", 
                        'Total Transactions', COLORS['primary'])
        
        create_stat_card(fig.add_subplot(gs[0, 1]), 
                        f"${metrics['total_amount']/1000000:.1f}M", 
                        'Total Volume', COLORS['success'])
        
        create_stat_card(fig.add_subplot(gs[0, 2]), 
                        f"{metrics['total_fraud_alerts']:,}", 
                        'Fraud Alerts', COLORS['danger'])
        
        create_stat_card(fig.add_subplot(gs[0, 3]), 
                        f"{metrics['fraud_rate']:.2f}%", 
                        'Fraud Rate', COLORS['warning'])
        
        # Second row: Additional metrics
        create_stat_card(fig.add_subplot(gs[1, 0]), 
                        f"{metrics['validated_count']:,}", 
                        'Validated Txns', COLORS['success'])
        
        create_stat_card(fig.add_subplot(gs[1, 1]), 
                        f"${stats['transactions'].get('avg_amount', 0):,.0f}", 
                        'Avg Transaction', COLORS['primary'])
        
        create_stat_card(fig.add_subplot(gs[1, 2]), 
                        f"{stats['transactions'].get('unique_users', 0):,}", 
                        'Unique Users', COLORS['primary'])
        
        create_stat_card(fig.add_subplot(gs[1, 3]), 
                        f"{stats['transactions'].get('category_count', 0)}", 
                        'Categories', COLORS['primary'])
        
        # Financial Overview Section
        ax_finance = fig.add_subplot(gs[2:4, :2])
        ax_finance.set_xlim(0, 1)
        ax_finance.set_ylim(0, 1)
        ax_finance.axis('off')
        
        # Section header
        ax_finance.add_patch(Rectangle((0, 0.85), 1, 0.15, 
                                       facecolor=COLORS['light'], 
                                       transform=ax_finance.transAxes))
        ax_finance.text(0.03, 0.925, 'FINANCIAL OVERVIEW', fontsize=12, 
                       fontweight='700', color=COLORS['dark'], 
                       transform=ax_finance.transAxes)
        
        # Financial details
        financial_items = [
            ('Total Transaction Value', f"${metrics['total_amount']:,.2f}"),
            ('Fraud Amount Detected', f"${metrics['fraud_amount']:,.2f}"),
            ('Validated Amount', f"${metrics['validated_amount']:,.2f}"),
            ('Reconciliation Difference', f"${abs(metrics['amount_reconciliation']):,.2f}")
        ]
        
        y_pos = 0.7
        for label, value in financial_items:
            ax_finance.text(0.05, y_pos, label, fontsize=10, 
                           fontweight='500', color=COLORS['medium'], 
                           transform=ax_finance.transAxes)
            ax_finance.text(0.95, y_pos, value, fontsize=11, 
                           fontweight='700', color=COLORS['dark'], 
                           ha='right', transform=ax_finance.transAxes)
            ax_finance.plot([0.05, 0.95], [y_pos - 0.08, y_pos - 0.08], 
                           color=COLORS['border'], linewidth=0.5, 
                           transform=ax_finance.transAxes)
            y_pos -= 0.18
        
        # System Status Section
        ax_status = fig.add_subplot(gs[2:4, 2:])
        ax_status.set_xlim(0, 1)
        ax_status.set_ylim(0, 1)
        ax_status.axis('off')
        
        # Section header
        ax_status.add_patch(Rectangle((0, 0.85), 1, 0.15, 
                                     facecolor=COLORS['light'], 
                                     transform=ax_status.transAxes))
        ax_status.text(0.03, 0.925, 'SYSTEM STATUS', fontsize=12, 
                      fontweight='700', color=COLORS['dark'], 
                      transform=ax_status.transAxes)
        
        # Status items
        status_items = [
            ('Expected Validated Count', f"{metrics['expected_validated']:,}"),
            ('Actual Validated Count', f"{metrics['validated_count']:,}"),
            ('Validation Gap', f"{metrics['validation_gap']:,}"),
            ('Fraud Types Detected', f"{stats['fraud_alerts'].get('fraud_type_count', 0)}")
        ]
        
        y_pos = 0.7
        for label, value in status_items:
            ax_status.text(0.05, y_pos, label, fontsize=10, 
                          fontweight='500', color=COLORS['medium'], 
                          transform=ax_status.transAxes)
            ax_status.text(0.95, y_pos, value, fontsize=11, 
                          fontweight='700', color=COLORS['dark'], 
                          ha='right', transform=ax_status.transAxes)
            ax_status.plot([0.05, 0.95], [y_pos - 0.08, y_pos - 0.08], 
                          color=COLORS['border'], linewidth=0.5, 
                          transform=ax_status.transAxes)
            y_pos -= 0.18
        
        # Key Insights Section
        ax_insights = fig.add_subplot(gs[4, :])
        ax_insights.set_xlim(0, 1)
        ax_insights.set_ylim(0, 1)
        ax_insights.axis('off')
        
        ax_insights.add_patch(Rectangle((0, 0), 1, 1, 
                                       facecolor=COLORS['primary_light'], 
                                       transform=ax_insights.transAxes))
        
        insights_text = f"""KEY FINDINGS:  {metrics['fraud_rate']:.2f}% fraud detection rate  •  {metrics['validation_gap']:,} transactions pending validation  •  ${metrics['fraud_amount']:,.0f} in detected fraud  •  {stats['transactions'].get('unique_users', 0):,} users monitored"""
        
        ax_insights.text(0.5, 0.5, insights_text, fontsize=10, 
                        fontweight='500', color=COLORS['dark'], 
                        ha='center', va='center', transform=ax_insights.transAxes,
                        wrap=True)
        
        pdf.savefig(fig, facecolor=COLORS['white'])
        plt.close()
        
        # ============================================================
        # PAGE 2: FRAUD ANALYSIS
        # ============================================================
        fig = plt.figure(figsize=(11, 8.5))
        add_page_header(fig, 'Fraud Type Analysis', 2)
        
        if stats['fraud_by_type']:
            gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3, 
                                 top=0.88, bottom=0.06, left=0.08, right=0.94)
            
            fraud_types = [f['fraud_type'] for f in stats['fraud_by_type']]
            fraud_counts = [f['count'] for f in stats['fraud_by_type']]
            
            # Color mapping
            color_map = {
                0: COLORS['danger'],
                1: COLORS['warning'],
                2: COLORS['primary'],
                3: COLORS['success'],
            }
            colors = [color_map.get(i, COLORS['medium']) for i in range(len(fraud_types))]
            
            # Donut chart
            ax1 = fig.add_subplot(gs[0, 0])
            wedges, texts, autotexts = ax1.pie(fraud_counts, labels=fraud_types, 
                   autopct='%1.1f%%', startangle=90, colors=colors,
                   wedgeprops=dict(width=0.4, edgecolor='white', linewidth=3),
                   textprops={'fontsize': 10, 'fontweight': '600'})
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
            
            ax1.set_title('Fraud Distribution by Type', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            
            # Bar chart
            ax2 = fig.add_subplot(gs[0, 1])
            y_pos = np.arange(len(fraud_types))
            bars = ax2.barh(y_pos, fraud_counts, height=0.6, color=colors, 
                           edgecolor='white', linewidth=2)
            
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(fraud_types, fontsize=10, fontweight='500')
            ax2.set_xlabel('Number of Alerts', fontsize=11, fontweight='600')
            ax2.set_title('Alert Count by Type', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color(COLORS['border'])
            ax2.spines['bottom'].set_color(COLORS['border'])
            ax2.grid(axis='x', alpha=0.3, linestyle='-', linewidth=0.8)
            
            for i, (bar, count) in enumerate(zip(bars, fraud_counts)):
                width = bar.get_width()
                ax2.text(width + max(fraud_counts)*0.01, bar.get_y() + bar.get_height()/2,
                        f'{count:,}', va='center', fontsize=10, fontweight='600',
                        color=COLORS['dark'])
            
            # Detailed table
            ax3 = fig.add_subplot(gs[1:, :])
            ax3.axis('off')
            
            # Table header
            ax3.text(0.5, 0.97, 'Detailed Fraud Impact Analysis', fontsize=13, 
                    fontweight='700', ha='center', color=COLORS['dark'],
                    transform=ax3.transAxes)
            
            table_data = []
            for fraud_data in stats['fraud_impact']:
                row = [
                    fraud_data['fraud_type'],
                    f"{fraud_data['count']:,}",
                    f"${fraud_data['total_amount']:,.2f}" if fraud_data['total_amount'] > 0 else "—",
                    f"${fraud_data['avg_amount']:,.2f}" if fraud_data['avg_amount'] > 0 else "—",
                    f"${fraud_data['max_amount']:,.2f}" if fraud_data['max_amount'] > 0 else "—"
                ]
                table_data.append(row)
            
            table = ax3.table(cellText=table_data, 
                            colLabels=['Fraud Type', 'Alert Count', 'Total Amount', 
                                      'Average Amount', 'Max Amount'],
                            loc='center', cellLoc='left',
                            colWidths=[0.22, 0.15, 0.21, 0.21, 0.21],
                            bbox=[0.05, 0.1, 0.9, 0.82])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            
            # Style header
            for i in range(5):
                cell = table[(0, i)]
                cell.set_facecolor(COLORS['dark'])
                cell.set_text_props(weight='700', color='white', fontsize=11)
                cell.set_height(0.08)
                cell.set_edgecolor('white')
                cell.set_linewidth(2)
            
            # Style data rows
            for i in range(1, len(table_data) + 1):
                for j in range(5):
                    cell = table[(i, j)]
                    cell.set_facecolor(COLORS['light'] if i % 2 == 0 else COLORS['white'])
                    cell.set_edgecolor(COLORS['border'])
                    cell.set_linewidth(1)
                    cell.set_height(0.07)
                    if j == 0:
                        cell.set_text_props(weight='600')
        
        pdf.savefig(fig, facecolor=COLORS['white'])
        plt.close()
        
        # ============================================================
        # PAGE 3: MERCHANT CATEGORY ANALYSIS
        # ============================================================
        fig = plt.figure(figsize=(11, 8.5))
        add_page_header(fig, 'Merchant Category Analysis', 3)
        
        if stats['fraud_by_merchant'] and stats['fraud_rate_by_category']:
            gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.35, 
                                 top=0.88, bottom=0.06, left=0.08, right=0.94)
            
            categories = [f['merchant_category'] for f in stats['fraud_by_merchant']]
            fraud_counts = [f['fraud_count'] for f in stats['fraud_by_merchant']]
            fraud_amounts = [f['fraud_amount'] for f in stats['fraud_by_merchant']]
            
            # Fraud count bar chart
            ax1 = fig.add_subplot(gs[0, 0])
            x_pos = np.arange(len(categories))
            bars = ax1.bar(x_pos, fraud_counts, width=0.7, 
                          color=COLORS['danger'], alpha=0.9, 
                          edgecolor='white', linewidth=2)
            
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=9)
            ax1.set_ylabel('Fraud Alert Count', fontsize=11, fontweight='600')
            ax1.set_title('Fraud Alerts by Category', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color(COLORS['border'])
            ax1.spines['bottom'].set_color(COLORS['border'])
            ax1.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.8)
            ax1.set_axisbelow(True)
            
            # Fraud amount bar chart
            ax2 = fig.add_subplot(gs[0, 1])
            bars = ax2.bar(x_pos, fraud_amounts, width=0.7, 
                          color=COLORS['warning'], alpha=0.9, 
                          edgecolor='white', linewidth=2)
            
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(categories, rotation=45, ha='right', fontsize=9)
            ax2.set_ylabel('Fraud Amount ($)', fontsize=11, fontweight='600')
            ax2.set_title('Fraud Amount by Category', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color(COLORS['border'])
            ax2.spines['bottom'].set_color(COLORS['border'])
            ax2.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.8)
            ax2.set_axisbelow(True)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
            
            # Fraud rate horizontal bar
            ax3 = fig.add_subplot(gs[1, :])
            rate_categories = [f['merchant_category'] for f in stats['fraud_rate_by_category']]
            fraud_rates = [float(f['fraud_rate_pct']) for f in stats['fraud_rate_by_category']]
            
            # Color by severity
            rate_colors = []
            for rate in fraud_rates:
                if rate < 5:
                    rate_colors.append(COLORS['success'])
                elif rate < 10:
                    rate_colors.append(COLORS['warning'])
                else:
                    rate_colors.append(COLORS['danger'])
            
            y_pos = np.arange(len(rate_categories))
            bars = ax3.barh(y_pos, fraud_rates, height=0.65, color=rate_colors, 
                           alpha=0.9, edgecolor='white', linewidth=2)
            
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(rate_categories, fontsize=10, fontweight='500')
            ax3.set_xlabel('Fraud Rate (%)', fontsize=11, fontweight='600')
            ax3.set_title('Fraud Rate by Merchant Category', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(COLORS['border'])
            ax3.spines['bottom'].set_color(COLORS['border'])
            ax3.grid(axis='x', alpha=0.3, linestyle='-', linewidth=0.8)
            ax3.set_axisbelow(True)
            
            for i, (bar, rate) in enumerate(zip(bars, fraud_rates)):
                width = bar.get_width()
                ax3.text(width + max(fraud_rates)*0.01, bar.get_y() + bar.get_height()/2,
                        f'{rate:.1f}%', va='center', fontsize=9, fontweight='600',
                        color=COLORS['dark'])
            
            # Summary table
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            
            table_data = []
            for cat_data in stats['fraud_by_merchant'][:6]:
                rate_data = next((r for r in stats['fraud_rate_by_category'] 
                                if r['merchant_category'] == cat_data['merchant_category']), None)
                row = [
                    cat_data['merchant_category'],
                    f"{cat_data['fraud_count']:,}",
                    f"${cat_data['fraud_amount']:,.2f}",
                    f"${cat_data['avg_fraud_amount']:,.2f}",
                    f"{rate_data['fraud_rate_pct']:.2f}%" if rate_data else "—"
                ]
                table_data.append(row)
            
            table = ax4.table(cellText=table_data, 
                            colLabels=['Category', 'Fraud Count', 'Total Amount', 
                                      'Avg Amount', 'Fraud Rate'],
                            loc='center', cellLoc='left',
                            colWidths=[0.24, 0.16, 0.22, 0.22, 0.16],
                            bbox=[0.05, 0.05, 0.9, 0.9])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            
            for i in range(5):
                cell = table[(0, i)]
                cell.set_facecolor(COLORS['dark'])
                cell.set_text_props(weight='700', color='white', fontsize=11)
                cell.set_height(0.12)
                cell.set_edgecolor('white')
                cell.set_linewidth(2)
            
            for i in range(1, len(table_data) + 1):
                for j in range(5):
                    cell = table[(i, j)]
                    cell.set_facecolor(COLORS['light'] if i % 2 == 0 else COLORS['white'])
                    cell.set_edgecolor(COLORS['border'])
                    cell.set_linewidth(1)
                    if j == 0:
                        cell.set_text_props(weight='600')
        
        pdf.savefig(fig, facecolor=COLORS['white'])
        plt.close()
        
        # ============================================================
        # PAGE 4: TEMPORAL PATTERNS & RISK ANALYSIS
        # ============================================================
        fig = plt.figure(figsize=(11, 8.5))
        add_page_header(fig, 'Temporal Patterns & Risk Analysis', 4)
        
        gs = fig.add_gridspec(2, 1, height_ratios=[1.4, 1], hspace=0.4,
                             top=0.88, bottom=0.06, left=0.08, right=0.94)
        
        # Hourly pattern
        if stats['hourly_pattern']:
            ax1 = fig.add_subplot(gs[0, 0])
            hours = [int(h['hour']) for h in stats['hourly_pattern']]
            tx_counts = [h['tx_count'] for h in stats['hourly_pattern']]
            fraud_counts = [h['fraud_count'] for h in stats['hourly_pattern']]
            
            x = np.arange(len(hours))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, tx_counts, width, 
                           label='Total Transactions', 
                           color=COLORS['primary'], alpha=0.9, 
                           edgecolor='white', linewidth=1.5)
            bars2 = ax1.bar(x + width/2, fraud_counts, width, 
                           label='Fraud Transactions', 
                           color=COLORS['danger'], alpha=0.9, 
                           edgecolor='white', linewidth=1.5)
            
            ax1.set_xlabel('Hour of Day', fontsize=11, fontweight='600')
            ax1.set_ylabel('Transaction Count', fontsize=11, fontweight='600')
            ax1.set_title('Transaction & Fraud Pattern by Hour', fontsize=13, 
                         fontweight='700', pad=20, color=COLORS['dark'])
            ax1.set_xticks(x)
            ax1.set_xticklabels([f'{h:02d}:00' for h in hours], 
                               rotation=45, ha='right', fontsize=9)
            ax1.legend(fontsize=10, loc='upper left', framealpha=0.95, 
                      edgecolor=COLORS['border'], fancybox=False)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color(COLORS['border'])
            ax1.spines['bottom'].set_color(COLORS['border'])
            ax1.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.8)
            ax1.set_axisbelow(True)
        
        # High-risk users table
        if stats['high_risk_users']:
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.axis('off')
            
            ax2.text(0.5, 0.96, 'Top 10 High-Risk Users (Multiple Fraud Alerts)', 
                    fontsize=13, fontweight='700', ha='center', 
                    color=COLORS['dark'], transform=ax2.transAxes)
            
            table_data = []
            for user_data in stats['high_risk_users'][:10]:
                user_id = user_data['user_id']
                if len(user_id) > 28:
                    user_id = user_id[:25] + '...'
                row = [
                    user_id,
                    f"{user_data['fraud_count']:,}",
                    f"${user_data['total_fraud_amount']:,.2f}",
                    f"{user_data['categories_affected']}"
                ]
                table_data.append(row)
            
            table = ax2.table(cellText=table_data, 
                            colLabels=['User ID', 'Fraud Count', 
                                      'Total Fraud Amount', 'Categories Affected'],
                            loc='center', cellLoc='left',
                            colWidths=[0.38, 0.18, 0.26, 0.18],
                            bbox=[0.05, 0.05, 0.9, 0.88])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            
            for i in range(4):
                cell = table[(0, i)]
                cell.set_facecolor(COLORS['danger'])
                cell.set_text_props(weight='700', color='white', fontsize=10)
                cell.set_height(0.09)
                cell.set_edgecolor('white')
                cell.set_linewidth(2)
            
            for i in range(1, len(table_data) + 1):
                for j in range(4):
                    cell = table[(i, j)]
                    cell.set_facecolor(COLORS['danger_light'] if i % 2 == 0 else COLORS['white'])
                    cell.set_edgecolor(COLORS['border'])
                    cell.set_linewidth(1)
                    cell.set_height(0.08)
                    if j == 0:
                        cell.set_text_props(fontfamily='monospace', fontsize=8)
        
        pdf.savefig(fig, facecolor=COLORS['white'])
        plt.close()
        
        # ============================================================
        # PAGE 5: RECONCILIATION & FINANCIAL OVERVIEW
        # ============================================================
        fig = plt.figure(figsize=(11, 8.5))
        add_page_header(fig, 'Reconciliation & Financial Overview', 5)
        
        gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.35, 
                             height_ratios=[1, 1.2, 1.3],
                             top=0.88, bottom=0.06, left=0.08, right=0.94)
        
        # Reconciliation flow
        ax1 = fig.add_subplot(gs[0, :])
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        
        # Section background
        ax1.add_patch(Rectangle((0.02, 0.1), 0.96, 0.85, 
                               facecolor=COLORS['light'], 
                               edgecolor=COLORS['border'], linewidth=2,
                               transform=ax1.transAxes))
        
        ax1.text(0.5, 0.85, 'TRANSACTION RECONCILIATION FLOW', 
                fontsize=12, fontweight='700', ha='center', 
                color=COLORS['dark'], transform=ax1.transAxes)
        
        # Flow items
        flow_items = [
            ('Total Transactions', f"{metrics['total_transactions']:,}", 
             f"${metrics['total_amount']:,.2f}"),
            ('Less: Fraud Detected', f"({metrics['total_fraud_alerts']:,})", 
             f"(${metrics['fraud_amount']:,.2f})"),
            ('Expected Validated', f"{metrics['expected_validated']:,}", ''),
            ('Actual Validated', f"{metrics['validated_count']:,}", 
             f"${metrics['validated_amount']:,.2f}"),
        ]
        
        y_pos = 0.65
        for label, count, amount in flow_items:
            ax1.text(0.1, y_pos, label, fontsize=10, fontweight='500',
                    color=COLORS['dark'], transform=ax1.transAxes)
            ax1.text(0.55, y_pos, count, fontsize=10, fontweight='600',
                    color=COLORS['dark'], transform=ax1.transAxes, 
                    family='monospace')
            if amount:
                ax1.text(0.88, y_pos, amount, fontsize=10, fontweight='600',
                        color=COLORS['dark'], ha='right', 
                        transform=ax1.transAxes, family='monospace')
            y_pos -= 0.16
        
        # Status indicator
        recon_ok = abs(metrics['amount_reconciliation']) < 100
        status_color = COLORS['success'] if recon_ok else COLORS['warning']
        status_text = '✓ RECONCILED' if recon_ok else '⚠ REVIEW NEEDED'
        
        ax1.add_patch(Rectangle((0.35, 0.02), 0.3, 0.1, 
                               facecolor=status_color, alpha=0.2,
                               edgecolor=status_color, linewidth=2,
                               transform=ax1.transAxes))
        ax1.text(0.5, 0.07, status_text, fontsize=11, fontweight='700',
                color=status_color, ha='center', transform=ax1.transAxes)
        
        # Transaction status pie
        ax2 = fig.add_subplot(gs[1, 0])
        labels = ['Validated', 'Fraud', 'Pending']
        sizes = [metrics['validated_count'], metrics['total_fraud_alerts'], 
                max(0, metrics['validation_gap'])]
        colors_pie = [COLORS['success'], COLORS['danger'], COLORS['warning']]
        
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, 
               autopct='%1.1f%%', startangle=90, colors=colors_pie,
               wedgeprops=dict(width=0.4, edgecolor='white', linewidth=3),
               textprops={'fontsize': 10, 'fontweight': '600'})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        ax2.set_title('Transaction Status', fontsize=12, 
                     fontweight='700', pad=20, color=COLORS['dark'])
        
        # Amount distribution pie
        ax3 = fig.add_subplot(gs[1, 1])
        amount_sizes = [metrics['validated_amount'], metrics['fraud_amount'], 
                       abs(metrics['amount_reconciliation'])]
        
        wedges, texts, autotexts = ax3.pie(amount_sizes, labels=labels, 
               autopct='%1.1f%%', startangle=90, colors=colors_pie,
               wedgeprops=dict(width=0.4, edgecolor='white', linewidth=3),
               textprops={'fontsize': 10, 'fontweight': '600'})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        ax3.set_title('Amount Distribution', fontsize=12, 
                     fontweight='700', pad=20, color=COLORS['dark'])
        
        # Category comparison
        if stats['transactions_by_merchant']:
            ax4 = fig.add_subplot(gs[2, :])
            
            categories = [m['merchant_category'] for m in stats['transactions_by_merchant']]
            tx_counts = [m['tx_count'] for m in stats['transactions_by_merchant']]
            
            fraud_map = {f['merchant_category']: f['fraud_count'] 
                        for f in stats['fraud_by_merchant']}
            fraud_counts = [fraud_map.get(cat, 0) for cat in categories]
            
            x = np.arange(len(categories))
            width = 0.38
            
            bars1 = ax4.bar(x - width/2, tx_counts, width, 
                          label='Total Transactions', 
                          color=COLORS['primary'], alpha=0.9, 
                          edgecolor='white', linewidth=1.5)
            bars2 = ax4.bar(x + width/2, fraud_counts, width, 
                          label='Fraud Transactions', 
                          color=COLORS['danger'], alpha=0.9, 
                          edgecolor='white', linewidth=1.5)
            
            ax4.set_xlabel('Merchant Category', fontsize=11, fontweight='600')
            ax4.set_ylabel('Transaction Count', fontsize=11, fontweight='600')
            ax4.set_title('Transaction vs Fraud Comparison by Category', 
                         fontsize=13, fontweight='700', pad=20, 
                         color=COLORS['dark'])
            ax4.set_xticks(x)
            ax4.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
            ax4.legend(fontsize=10, loc='upper right', framealpha=0.95, 
                      edgecolor=COLORS['border'], fancybox=False)
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.spines['left'].set_color(COLORS['border'])
            ax4.spines['bottom'].set_color(COLORS['border'])
            ax4.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.8)
            ax4.set_axisbelow(True)
        
        pdf.savefig(fig, facecolor=COLORS['white'])
        plt.close()
    
    print(f"{'='*60}")
    print(f"✓ Modern report generated successfully")
    print(f"{'='*60}")
    print(f"Location: {output_path}\n")
    return output_path

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate modern comprehensive analytical report")
    parser.add_argument("--output", "-o", type=str, help="Custom output path for PDF report")
    
    args = parser.parse_args()
    
    if args.output:
        generate_comprehensive_pdf(args.output)
    else:
        generate_comprehensive_pdf()