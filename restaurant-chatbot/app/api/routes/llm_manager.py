"""
LLM Manager Monitoring API
===========================
Real-time monitoring of all 20 OpenAI account usage and resource allocation
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime

from app.ai_services.llm_manager import get_llm_manager

router = APIRouter()


@router.get("/llm-manager/status")
async def get_llm_manager_status() -> Dict[str, Any]:
    """
    Get comprehensive LLM Manager status with all account usage statistics.

    Returns detailed information about:
    - Total accounts configured
    - Per-account usage for both gpt-4o and gpt-4o-mini
    - Cooldown states
    - Current RPM/TPM utilization
    - Available capacity
    """
    try:
        manager = get_llm_manager()

        # Get all account statistics
        all_stats = manager.get_all_usage_stats()

        # Get model-specific stats
        gpt4o_stats = manager.get_model_usage_stats("gpt-4o")
        gpt4o_mini_stats = manager.get_model_usage_stats("gpt-4o-mini")

        # Calculate aggregate statistics
        total_accounts = len(manager.accounts)

        # Count available accounts per model
        gpt4o_available = sum(1 for s in gpt4o_stats if s['cooldown_state'] == 'available')
        gpt4o_cooling = sum(1 for s in gpt4o_stats if s['cooldown_state'] == 'cooling_down')

        gpt4o_mini_available = sum(1 for s in gpt4o_mini_stats if s['cooldown_state'] == 'available')
        gpt4o_mini_cooling = sum(1 for s in gpt4o_mini_stats if s['cooldown_state'] == 'cooling_down')

        # Calculate total current usage
        total_gpt4o_rpm = sum(s['current_rpm'] for s in gpt4o_stats)
        total_gpt4o_tpm = sum(s['current_tpm'] for s in gpt4o_stats)

        total_gpt4o_mini_rpm = sum(s['current_rpm'] for s in gpt4o_mini_stats)
        total_gpt4o_mini_tpm = sum(s['current_tpm'] for s in gpt4o_mini_stats)

        # Calculate total capacity
        total_gpt4o_rpm_capacity = sum(s['rpm_limit'] for s in gpt4o_stats)
        total_gpt4o_tpm_capacity = sum(s['tpm_limit'] for s in gpt4o_stats)

        total_gpt4o_mini_rpm_capacity = sum(s['rpm_limit'] for s in gpt4o_mini_stats)
        total_gpt4o_mini_tpm_capacity = sum(s['tpm_limit'] for s in gpt4o_mini_stats)

        # Calculate average utilization
        avg_gpt4o_rpm_util = (total_gpt4o_rpm / total_gpt4o_rpm_capacity * 100) if total_gpt4o_rpm_capacity > 0 else 0
        avg_gpt4o_tpm_util = (total_gpt4o_tpm / total_gpt4o_tpm_capacity * 100) if total_gpt4o_tpm_capacity > 0 else 0

        avg_gpt4o_mini_rpm_util = (total_gpt4o_mini_rpm / total_gpt4o_mini_rpm_capacity * 100) if total_gpt4o_mini_rpm_capacity > 0 else 0
        avg_gpt4o_mini_tpm_util = (total_gpt4o_mini_tpm / total_gpt4o_mini_tpm_capacity * 100) if total_gpt4o_mini_tpm_capacity > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "manager_config": {
                "total_accounts": total_accounts,
                "cooldown_seconds": manager._cooldown_seconds,
                "retry_timeout_seconds": manager._retry_timeout,
                "retry_poll_seconds": manager._retry_poll_interval
            },
            "summary": {
                "gpt4o": {
                    "accounts_available": gpt4o_available,
                    "accounts_cooling_down": gpt4o_cooling,
                    "total_current_rpm": total_gpt4o_rpm,
                    "total_current_tpm": total_gpt4o_tpm,
                    "total_rpm_capacity": total_gpt4o_rpm_capacity,
                    "total_tpm_capacity": total_gpt4o_tpm_capacity,
                    "rpm_utilization_percent": round(avg_gpt4o_rpm_util, 2),
                    "tpm_utilization_percent": round(avg_gpt4o_tpm_util, 2),
                    "health_status": "healthy" if gpt4o_available > 0 else "critical"
                },
                "gpt4o_mini": {
                    "accounts_available": gpt4o_mini_available,
                    "accounts_cooling_down": gpt4o_mini_cooling,
                    "total_current_rpm": total_gpt4o_mini_rpm,
                    "total_current_tpm": total_gpt4o_mini_tpm,
                    "total_rpm_capacity": total_gpt4o_mini_rpm_capacity,
                    "total_tpm_capacity": total_gpt4o_mini_tpm_capacity,
                    "rpm_utilization_percent": round(avg_gpt4o_mini_rpm_util, 2),
                    "tpm_utilization_percent": round(avg_gpt4o_mini_tpm_util, 2),
                    "health_status": "healthy" if gpt4o_mini_available > 0 else "critical"
                }
            },
            "accounts": all_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLM manager status: {str(e)}")


@router.get("/llm-manager/accounts/{account_number}")
async def get_account_details(account_number: int) -> Dict[str, Any]:
    """
    Get detailed usage statistics for a specific account.

    Args:
        account_number: Account number (1-20)

    Returns:
        Detailed statistics for both gpt-4o and gpt-4o-mini for this account
    """
    try:
        manager = get_llm_manager()

        if account_number < 1 or account_number > len(manager.accounts):
            raise HTTPException(
                status_code=404,
                detail=f"Account {account_number} not found. Valid range: 1-{len(manager.accounts)}"
            )

        # Get the specific account (account_number is 1-indexed, list is 0-indexed)
        account = manager.accounts[account_number - 1]

        return {
            "timestamp": datetime.now().isoformat(),
            "account_number": account_number,
            "api_key_prefix": f"...{account.api_key[-10:]}" if len(account.api_key) > 10 else "***",
            "gpt4o": account.gpt4o_tracker.get_current_usage(),
            "gpt4o_mini": account.gpt4o_mini_tracker.get_current_usage()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get account details: {str(e)}")


@router.get("/llm-manager/model/{model_name}")
async def get_model_stats(model_name: str) -> Dict[str, Any]:
    """
    Get usage statistics for a specific model across all accounts.

    Args:
        model_name: Model name (gpt-4o or gpt-4o-mini)

    Returns:
        Usage statistics for this model across all 20 accounts
    """
    try:
        # Normalize model name
        if model_name.lower() not in ["gpt-4o", "gpt-4o-mini", "gpt4o", "gpt4o-mini"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model name. Use 'gpt-4o' or 'gpt-4o-mini'"
            )

        # Normalize to standard format
        normalized_model = "gpt-4o" if "mini" not in model_name.lower() else "gpt-4o-mini"

        manager = get_llm_manager()
        model_stats = manager.get_model_usage_stats(normalized_model)

        # Calculate aggregates
        total_accounts = len(model_stats)
        available_accounts = sum(1 for s in model_stats if s['cooldown_state'] == 'available')
        cooling_accounts = sum(1 for s in model_stats if s['cooldown_state'] == 'cooling_down')

        total_rpm = sum(s['current_rpm'] for s in model_stats)
        total_tpm = sum(s['current_tpm'] for s in model_stats)

        total_rpm_capacity = sum(s['rpm_limit'] for s in model_stats)
        total_tpm_capacity = sum(s['tpm_limit'] for s in model_stats)

        return {
            "timestamp": datetime.now().isoformat(),
            "model": normalized_model,
            "summary": {
                "total_accounts": total_accounts,
                "accounts_available": available_accounts,
                "accounts_cooling_down": cooling_accounts,
                "total_current_rpm": total_rpm,
                "total_current_tpm": total_tpm,
                "total_rpm_capacity": total_rpm_capacity,
                "total_tpm_capacity": total_tpm_capacity,
                "rpm_utilization_percent": round((total_rpm / total_rpm_capacity * 100), 2) if total_rpm_capacity > 0 else 0,
                "tpm_utilization_percent": round((total_tpm / total_tpm_capacity * 100), 2) if total_tpm_capacity > 0 else 0
            },
            "accounts": model_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model stats: {str(e)}")
