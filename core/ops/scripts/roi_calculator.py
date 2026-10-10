#!/usr/bin/env python3
"""
XORAS::OS — Enterprise Interactive ROI & TCO Calculator
Calculates Direct Operational Savings, Stochastic Tax Reduction, Defect Mitigation Savings,
Total Cost of Ownership (TCO), and Net 12-Month Return on Investment (ROI %).
"""

import sys
import json

def calculate_roi(
    monthly_tasks=1000,
    human_hours_per_task=2.5,
    loaded_hourly_rate=85.0,
    agent_automation_rate=0.75,
    agent_cost_per_task=1.20,
    reopen_rate_reduction=0.85, # 85% reduction in reopens via MARS gates
    annual_hardware_and_api_cost=15000.0,
    implementation_and_training_cost=12000.0
):
    print("=" * 80)
    print("           XORAS::OS — 12-MONTH ENTERPRISE ROI & TCO CALCULATOR           ")
    print("=" * 80)
    
    annual_tasks = monthly_tasks * 12
    automated_tasks_annual = annual_tasks * agent_automation_rate
    
    # Baseline Human Cost
    baseline_annual_hours = annual_tasks * human_hours_per_task
    baseline_annual_cost = baseline_annual_hours * loaded_hourly_rate
    
    # XORAS::OS Operational Cost & Savings
    human_assisted_hours = (annual_tasks - automated_tasks_annual) * human_hours_per_task
    human_assisted_cost = human_assisted_hours * loaded_hourly_rate
    
    agent_execution_cost = automated_tasks_annual * agent_cost_per_task
    
    # Direct Labor Savings
    direct_labor_savings = baseline_annual_cost - (human_assisted_cost + agent_execution_cost)
    
    # Defect & Remediation Savings (Preventing 15x intent debt post-release)
    estimated_defects_prevented = automated_tasks_annual * 0.05 * reopen_rate_reduction
    defect_remediation_savings = estimated_defects_prevented * (loaded_hourly_rate * 8)
    
    total_annual_benefits = direct_labor_savings + defect_remediation_savings
    
    # Total Cost of Ownership (TCO)
    tco_year_1 = annual_hardware_and_api_cost + implementation_and_training_cost + (agent_execution_cost)
    net_savings = total_annual_benefits - (annual_hardware_and_api_cost + implementation_and_training_cost)
    net_roi_pct = (net_savings / tco_year_1) * 100.0
    
    # Output Results
    print(f"\n[1] OPERATIONAL BASELINE:")
    print(f"  • Monthly Task Volume: {monthly_tasks:,} tasks")
    print(f"  • Annual Task Volume: {annual_tasks:,} tasks")
    print(f"  • Baseline Human Cost: ${baseline_annual_cost:,.2f} ({baseline_annual_hours:,.0f} hours @ ${loaded_hourly_rate}/hr)")
    
    print(f"\n[2] XORAS::OS AUTOMATION PERFORMANCE:")
    print(f"  • Automation Rate: {agent_automation_rate * 100:.1f}% ({automated_tasks_annual:,.0f} tasks automated)")
    print(f"  • Agent Cost per Resolution: ${agent_cost_per_task:.2f}")
    print(f"  • Reopen & Defect Reduction: {reopen_rate_reduction * 100:.1f}%")
    
    print(f"\n[3] FINANCIAL BENEFITS (ANNUAL):")
    print(f"  • Direct Labor Cost Savings: ${direct_labor_savings:,.2f}")
    print(f"  • Intent Debt & Defect Prevention Savings: ${defect_remediation_savings:,.2f}")
    print(f"  • Total Gross Annual Benefits: ${total_annual_benefits:,.2f}")
    
    print(f"\n[4] TOTAL COST OF OWNERSHIP (TCO - YEAR 1):")
    print(f"  • Infrastructure & Token Costs: ${annual_hardware_and_api_cost:,.2f}")
    print(f"  • Implementation & Setup Overhead: ${implementation_and_training_cost:,.2f}")
    print(f"  • Total Year 1 Investment (TCO): ${tco_year_1:,.2f}")
    
    print(f"\n" + "=" * 80)
    print(f"  NET 12-MONTH SAVINGS:  ${net_savings:,.2f}")
    print(f"  PROJECTED 12-MONTH ROI: {net_roi_pct:,.1f}% (Payback Period: {12 / (total_annual_benefits / tco_year_1):.1f} Months)")
    print("=" * 80)
    
    return {
        "monthly_tasks": monthly_tasks,
        "automation_rate_pct": agent_automation_rate * 100,
        "baseline_annual_cost": baseline_annual_cost,
        "net_savings_year_1": net_savings,
        "tco_year_1": tco_year_1,
        "roi_pct": round(net_roi_pct, 1)
    }

if __name__ == "__main__":
    calculate_roi()
