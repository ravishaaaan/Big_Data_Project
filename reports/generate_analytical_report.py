#!/usr/bin/env python3
"""
Modern Comprehensive Analytical Report Generator
Enhanced with contemporary design and visual appeal
"""

import os
import sys
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_config import get_connection, query

# Modern color palette
COLORS = {
    'primary': '#6366f1', 'secondary': '#8b5cf6', 'success': '#10b981',
    'warning': '#f59e0b', 'danger': '#ef4444', 'info': '#3b82f6',
    'dark': '#1e293b', 'light': '#f8fafc', 'grad1': '#667eea', 'grad2': '#764ba2'
}

sns.set_style('white')
plt.rcParams.update({
    'figure.facecolor': '#ffffff', 'axes.facecolor': '#fafafa',
    'axes.edgecolor': '#e2e8f0', 'grid.color': '#e2e8f0',
    'grid.linestyle': '-', 'grid.linewidth': 0.5,
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
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

def add_modern_header(fig, title, subtitle=None):
    """Add modern gradient header"""
    ax = fig.add_axes([0, 0.94, 1, 0.06])
    ax.axis('off')
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(gradient, aspect='auto', cmap=plt.cm.colors.LinearSegmentedColormap.from_list('', [COLORS['grad1'], COLORS['grad2']]), extent=[0, 1, 0, 1])
    ax.text(0.5, 0.5, title, fontsize=18, fontweight='bold', color='white', ha='center', va='center', transform=ax.transAxes)
    if subtitle:
        ax.text(0.5, 0.15, subtitle, fontsize=10, color='white', ha='center', va='center', transform=ax.transAxes, alpha=0.9)

def create_metric_card(ax, label, value, subvalue=None, color=COLORS['primary']):
    """Create modern metric card"""
    ax.axis('off')
    card = FancyBboxPatch((0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.05", facecolor='white', 
                          edgecolor=color, linewidth=2, transform=ax.transAxes, zorder=1)
    ax.add_patch(card)
    shadow = FancyBboxPatch((0.06, 0.08), 0.9, 0.8, boxstyle="round,pad=0.05", facecolor='#00000008', 
                           edgecolor='none', transform=ax.transAxes, zorder=0)
    ax.add_patch(shadow)
    ax.text(0.5, 0.7, label, fontsize=11, color=COLORS['dark'], ha='center', transform=ax.transAxes, alpha=0.7, fontweight='500')
    ax.text(0.5, 0.45, value, fontsize=20, color=color, ha='center', transform=ax.transAxes, fontweight='bold')
    if subvalue:
        ax.text(0.5, 0.25, subvalue, fontsize=9, color=COLORS['dark'], ha='center', transform=ax.transAxes, alpha=0.6)

def generate_comprehensive_pdf(output_path=None):
    """Generate modern PDF report"""
    if not output_path:
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(OUTPUT_DIR, f'7_comprehensive_analytical_report_{ts}.pdf')
    
    print(f"\nGenerating Modern Report: {output_path}\n")
    
    stats = get_comprehensive_statistics()
    metrics = calculate_reconciliation_metrics(stats)
    
    with PdfPages(output_path) as pdf:
        # PAGE 1: DASHBOARD
        fig = plt.figure(figsize=(11, 8.5))
        add_modern_header(fig, 'Fraud Detection System', f"Analytical Report • {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
        
        gs = fig.add_gridspec(4, 3, hspace=0.4, wspace=0.3, top=0.90, bottom=0.05, left=0.06, right=0.94)
        
        create_metric_card(fig.add_subplot(gs[0, 0]), 'Total Transactions', f"{metrics['total_transactions']:,}", 
                          f"${metrics['total_amount']/1000:.0f}K Volume", COLORS['primary'])
        create_metric_card(fig.add_subplot(gs[0, 1]), 'Fraud Alerts', f"{metrics['total_fraud_alerts']:,}", 
                          f"{metrics['fraud_rate']:.2f}% Rate", COLORS['danger'])
        create_metric_card(fig.add_subplot(gs[0, 2]), 'Validated', f"{metrics['validated_count']:,}", 
                          f"${metrics['validated_amount']/1000:.0f}K Amount", COLORS['success'])
        create_metric_card(fig.add_subplot(gs[1, 0]), 'Unique Users', f"{stats['transactions'].get('unique_users', 0):,}", None, COLORS['info'])
        create_metric_card(fig.add_subplot(gs[1, 1]), 'Avg Transaction', f"${stats['transactions'].get('avg_amount', 0):,.2f}", None, COLORS['secondary'])
        create_metric_card(fig.add_subplot(gs[1, 2]), 'Categories', f"{stats['transactions'].get('category_count', 0)}", None, COLORS['warning'])
        
        ax7 = fig.add_subplot(gs[2:, :])
        ax7.axis('off')
        insight_box = FancyBboxPatch((0.05, 0.1), 0.9, 0.85, boxstyle="round,pad=0.02", facecolor='white', 
                                     edgecolor=COLORS['primary'], linewidth=2, transform=ax7.transAxes)
        ax7.add_patch(insight_box)
        ax7.text(0.5, 0.88, '📊 Key Insights', fontsize=14, fontweight='bold', ha='center', transform=ax7.transAxes, color=COLORS['dark'])
        
        insights = [
            f"• Fraud detection flagged {metrics['fraud_rate']:.2f}% of all transactions",
            f"• {metrics['validation_gap']:,} transactions pending validation",
            f"• Total fraud exposure: ${metrics['fraud_amount']:,.2f}",
            f"• Monitored {stats['transactions'].get('unique_users', 0):,} unique users",
            f"• Average transaction: ${stats['transactions'].get('avg_amount', 0):,.2f}",
            f"• Reconciliation difference: ${abs(metrics['amount_reconciliation']):,.2f}"
        ]
        y_pos = 0.72
        for insight in insights:
            ax7.text(0.12, y_pos, insight, fontsize=11, transform=ax7.transAxes, color=COLORS['dark'], alpha=0.85)
            y_pos -= 0.11
        
        pdf.savefig(fig, facecolor='white')
        plt.close()
        
        # PAGE 2: FRAUD ANALYSIS
        fig = plt.figure(figsize=(11, 8.5))
        add_modern_header(fig, 'Fraud Type Analysis')
        
        if stats['fraud_by_type']:
            gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3, top=0.90, bottom=0.08, left=0.08, right=0.94)
            
            fraud_types = [f['fraud_type'] for f in stats['fraud_by_type']]
            fraud_counts = [f['count'] for f in stats['fraud_by_type']]
            colors = [COLORS['danger'], COLORS['warning'], COLORS['info'], COLORS['secondary'], COLORS['primary']][:len(fraud_types)]
            
            ax1 = fig.add_subplot(gs[0, 0])
            wedges, texts, autotexts = ax1.pie(fraud_counts, labels=fraud_types, autopct='%1.1f%%', startangle=90, colors=colors, 
                   textprops={'fontsize': 10, 'fontweight': '600'}, wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            ax1.set_title('Fraud Distribution', fontsize=13, fontweight='bold', pad=15, color=COLORS['dark'])
            
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.barh(fraud_types, fraud_counts, color=colors, edgecolor='white', linewidth=2, height=0.6)
            ax2.set_xlabel('Alert Count', fontsize=11, fontweight='600', color=COLORS['dark'])
            ax2.set_title('Alerts by Type', fontsize=13, fontweight='bold', pad=15, color=COLORS['dark'])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.grid(axis='x', alpha=0.2)
            for i, v in enumerate(fraud_counts):
                ax2.text(v + max(fraud_counts)*0.02, i, f'{v:,}', va='center', fontsize=10, fontweight='600')
            
            ax3 = fig.add_subplot(gs[1, :])
            ax3.axis('off')
            ax3.text(0.5, 0.95, 'Fraud Impact Details', fontsize=13, fontweight='bold', ha='center', transform=ax3.transAxes, color=COLORS['dark'])
            
            table_data = [[f['fraud_type'], f"{f['count']:,}", 
                          f"${f['total_amount']:,.2f}" if f['total_amount'] > 0 else "N/A*",
                          f"${f['avg_amount']:,.2f}" if f['avg_amount'] > 0 else "N/A*",
                          f"${f['max_amount']:,.2f}" if f['max_amount'] > 0 else "N/A*"] 
                         for f in stats['fraud_impact']]
            
            table = ax3.table(cellText=table_data, colLabels=['Fraud Type', 'Alerts', 'Total', 'Avg', 'Max'],
                            loc='upper center', cellLoc='center', colWidths=[0.2, 0.15, 0.2, 0.2, 0.2],
                            bbox=[0.05, 0.1, 0.9, 0.75])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            
            for i in range(5):
                table[(0, i)].set_facecolor(COLORS['primary'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=11)
                table[(0, i)].set_edgecolor('white')
                table[(0, i)].set_linewidth(2)
            
            for i in range(1, len(table_data) + 1):
                for j in range(5):
                    table[(i, j)].set_facecolor('#fafafa' if i % 2 == 0 else 'white')
                    table[(i, j)].set_edgecolor('#e2e8f0')
        
        pdf.savefig(fig, facecolor='white')
        plt.close()
        
        # PAGE 3: MERCHANT ANALYSIS  
        fig = plt.figure(figsize=(11, 8.5))
        add_modern_header(fig, 'Merchant Category Analysis')
        
        if stats['fraud_by_merchant']:
            gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3, top=0.90, bottom=0.08, left=0.08, right=0.94)
            
            categories = [f['merchant_category'] for f in stats['fraud_by_merchant']]
            fraud_counts = [f['fraud_count'] for f in stats['fraud_by_merchant']]
            fraud_amounts = [f['fraud_amount'] for f in stats['fraud_by_merchant']]
            
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.bar(range(len(categories)), fraud_counts, color=COLORS['danger'], alpha=0.85, edgecolor='white', linewidth=2, width=0.7)
            ax1.set_xticks(range(len(categories)))
            ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=9)
            ax1.set_ylabel('Fraud Count', fontsize=11, fontweight='600')
            ax1.set_title('Fraud by Category', fontsize=12, fontweight='bold', pad=15)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.grid(axis='y', alpha=0.2)
            
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.bar(range(len(categories)), fraud_amounts, color=COLORS['warning'], alpha=0.85, edgecolor='white', linewidth=2, width=0.7)
            ax2.set_xticks(range(len(categories)))
            ax2.set_xticklabels(categories, rotation=45, ha='right', fontsize=9)
            ax2.set_ylabel('Amount ($)', fontsize=11, fontweight='600')
            ax2.set_title('Fraud Amount', fontsize=12, fontweight='bold', pad=15)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.grid(axis='y', alpha=0.2)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
            
            if stats['fraud_rate_by_category']:
                ax3 = fig.add_subplot(gs[1, :])
                rate_categories = [f['merchant_category'] for f in stats['fraud_rate_by_category']]
                fraud_rates = [float(f['fraud_rate_pct']) for f in stats['fraud_rate_by_category']]
                colors_grad = [COLORS['success'] if r < 5 else COLORS['warning'] if r < 10 else COLORS['danger'] for r in fraud_rates]
                
                ax3.barh(range(len(rate_categories)), fraud_rates, color=colors_grad, alpha=0.85, edgecolor='white', linewidth=2, height=0.6)
                ax3.set_yticks(range(len(rate_categories)))
                ax3.set_yticklabels(rate_categories, fontsize=10)
                ax3.set_xlabel('Fraud Rate (%)', fontsize=11, fontweight='600')
                ax3.set_title('Fraud Rate by Category', fontsize=12, fontweight='bold', pad=15)
                ax3.spines['top'].set_visible(False)
                ax3.spines['right'].set_visible(False)
                ax3.grid(axis='x', alpha=0.2)
                
                for i, v in enumerate(fraud_rates):
                    ax3.text(v + max(fraud_rates)*0.02, i, f'{v:.1f}%', va='center', fontsize=9, fontweight='600')
        
        pdf.savefig(fig, facecolor='white')
        plt.close()
        
        # PAGE 4: TEMPORAL & RISK
        fig = plt.figure(figsize=(11, 8.5))
        add_modern_header(fig, 'Temporal Patterns & Risk Analysis')
        
        gs = fig.add_gridspec(2, 1, height_ratios=[1.3, 1], hspace=0.35, top=0.90, bottom=0.08, left=0.08, right=0.94)
        
        if stats['hourly_pattern']:
            ax1 = fig.add_subplot(gs[0, 0])
            hours = [int(h['hour']) for h in stats['hourly_pattern']]
            tx_counts = [h['tx_count'] for h in stats['hourly_pattern']]
            fraud_counts = [h['fraud_count'] for h in stats['hourly_pattern']]
            x = np.arange(len(hours))
            width = 0.38
            
            ax1.bar(x - width/2, tx_counts, width, label='Total', color=COLORS['primary'], alpha=0.85, edgecolor='white', linewidth=1.5)
            ax1.bar(x + width/2, fraud_counts, width, label='Fraud', color=COLORS['danger'], alpha=0.85, edgecolor='white', linewidth=1.5)
            ax1.set_xlabel('Hour of Day', fontsize=11, fontweight='600')
            ax1.set_ylabel('Count', fontsize=11, fontweight='600')
            ax1.set_title('Hourly Pattern', fontsize=13, fontweight='bold', pad=15)
            ax1.set_xticks(x)
            ax1.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right', fontsize=9)
            ax1.legend(fontsize=10, loc='upper left', framealpha=0.95, edgecolor='#e2e8f0')
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.grid(axis='y', alpha=0.2)
        
        if stats['high_risk_users']:
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.axis('off')
            ax2.text(0.5, 0.95, 'Top 10 High-Risk Users', fontsize=13, fontweight='bold', ha='center', transform=ax2.transAxes)
            
            table_data = [[u['user_id'][:25] + '...' if len(u['user_id']) > 25 else u['user_id'],
                          f"{u['fraud_count']:,}", f"${u['total_fraud_amount']:,.2f}", f"{u['categories_affected']}"] 
                         for u in stats['high_risk_users'][:10]]
            
            table = ax2.table(cellText=table_data, colLabels=['User ID', 'Fraud Count', 'Amount', 'Categories'],
                            loc='upper center', cellLoc='center', colWidths=[0.35, 0.18, 0.27, 0.15],
                            bbox=[0.05, 0.05, 0.9, 0.85])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            
            for i in range(4):
                table[(0, i)].set_facecolor(COLORS['danger'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=10)
        
        pdf.savefig(fig, facecolor='white')
        plt.close()
        
        # PAGE 5: RECONCILIATION
        fig = plt.figure(figsize=(11, 8.5))
        add_modern_header(fig, 'Reconciliation & Financial Overview')
        
        gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.35, height_ratios=[0.8, 1, 1.2],
                             top=0.92, bottom=0.08, left=0.08, right=0.95)
        
        ax1 = fig.add_subplot(gs[0, :])
        ax1.axis('off')
        ax1.text(0.5, 0.9, 'RECONCILIATION STATUS', fontsize=13, fontweight='bold', ha='center', transform=ax1.transAxes,
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['success'], alpha=0.8))
        
        flow_data = [('Total Transactions:', f"{metrics['total_transactions']:,}", f"${metrics['total_amount']:,.2f}"),
                    ('Fraud Detected:', f"{metrics['total_fraud_alerts']:,}", f"${metrics['fraud_amount']:,.2f}"),
                    ('Validated:', f"{metrics['validated_count']:,}", f"${metrics['validated_amount']:,.2f}")]
        
        y_pos = 0.65
        for label, count, amount in flow_data:
            ax1.text(0.15, y_pos, label, fontsize=10, fontweight='bold', transform=ax1.transAxes)
            ax1.text(0.45, y_pos, count, fontsize=10, family='monospace', transform=ax1.transAxes)
            ax1.text(0.65, y_pos, amount, fontsize=10, family='monospace', transform=ax1.transAxes)
            y_pos -= 0.15
        
        recon_status = "✓ OK" if abs(metrics['amount_reconciliation']) < 100 else "⚠ MISMATCH"
        status_color = COLORS['success'] if abs(metrics['amount_reconciliation']) < 100 else COLORS['warning']
        ax1.text(0.15, 0.05, f"Gap: {metrics['validation_gap']:,} transactions", fontsize=9, style='italic', transform=ax1.transAxes)
        ax1.text(0.65, 0.05, f"Status: {recon_status}", fontsize=9, fontweight='bold', color=status_color, transform=ax1.transAxes)
        
        ax2 = fig.add_subplot(gs[1, 0])
        labels = ['Fraud', 'Validated', 'Pending']
        sizes = [metrics['total_fraud_alerts'], metrics['validated_count'], max(0, metrics['validation_gap'])]
        colors = [COLORS['danger'], COLORS['success'], COLORS['warning']]
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=(0.1, 0, 0),
               textprops={'fontsize': 10}, wedgeprops=dict(edgecolor='white', linewidth=2))
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax2.set_title('Transaction Status', fontsize=11, fontweight='bold', pad=10)
        
        ax3 = fig.add_subplot(gs[1, 1])
        amount_sizes = [metrics['fraud_amount'], metrics['validated_amount'], abs(metrics['amount_reconciliation'])]
        wedges, texts, autotexts = ax3.pie(amount_sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=(0.1, 0, 0),
               textprops={'fontsize': 10}, wedgeprops=dict(edgecolor='white', linewidth=2))
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax3.set_title('Amount Distribution', fontsize=11, fontweight='bold', pad=10)
        
        if stats['transactions_by_merchant']:
            ax4 = fig.add_subplot(gs[2, :])
            categories = [m['merchant_category'] for m in stats['transactions_by_merchant']]
            tx_counts = [m['tx_count'] for m in stats['transactions_by_merchant']]
            fraud_map = {f['merchant_category']: f['fraud_count'] for f in stats['fraud_by_merchant']}
            fraud_counts = [fraud_map.get(cat, 0) for cat in categories]
            x = np.arange(len(categories))
            width = 0.4
            
            ax4.bar(x - width/2, tx_counts, width, label='Total', color=COLORS['info'], alpha=0.8, edgecolor='white', linewidth=1.5)
            ax4.bar(x + width/2, fraud_counts, width, label='Fraud', color=COLORS['danger'], alpha=0.8, edgecolor='white', linewidth=1.5)
            ax4.set_xlabel('Merchant Category', fontsize=11, fontweight='600')
            ax4.set_ylabel('Transaction Count', fontsize=11, fontweight='600')
            ax4.set_title('Transaction vs Fraud Comparison', fontsize=12, fontweight='bold', pad=15)
            ax4.set_xticks(x)
            ax4.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
            ax4.legend(fontsize=10, loc='upper right', framealpha=0.9)
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.grid(axis='y', alpha=0.2)
        
        pdf.savefig(fig, facecolor='white')
        plt.close()
    
    print(f"✓ Modern report generated: {output_path}")
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