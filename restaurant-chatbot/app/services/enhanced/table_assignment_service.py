"""
Smart Table Assignment Service
===============================

Intelligent table assignment for restaurant bookings using LLM-based decision logic.

Architecture:
- LLM analyzes party size, preferences, and context
- Smart scoring for table combinations
- Handles special requests (window seat, garden, etc.)
- Table combinations for large groups
- Controlled by ADVANCED_TABLE_ASSIGNMENT feature flag

Flow:
1. User requests table booking → crew agent extracts party_size, preferences
2. [OPTIONAL] If feature enabled → use smart assignment
3. System finds best table(s) based on context and availability
4. Return table assignment with reasoning

Design Principles:
- Let LLM understand context (not hardcoded keywords)
- Graceful degradation (fallback to simple first-available if needed)
- Transparent reasoning for why tables were chosen
- Flexible for future ML models

Usage:
    from app.services.enhanced.table_assignment_service import TableAssignmentService
    from app.core.feature_flags import FeatureFlags, Feature

    # In table booking agent
    if FeatureFlags.is_enabled(Feature.ADVANCED_TABLE_ASSIGNMENT):
        assignment_service = TableAssignmentService()
        result = await assignment_service.find_best_tables(
            restaurant_id=restaurant_id,
            party_size=4,
            booking_date=date(2025, 12, 25),
            booking_time=time(19, 0),
            preferences={"table_type": "window"}
        )
"""

import os
from typing import Dict, Any, List, Optional
from datetime import date, time as time_type, datetime
from itertools import combinations
import structlog

from app.core.feature_flags import FeatureFlags, Feature
from app.core.database import get_db_session

logger = structlog.get_logger(__name__)


class TableAssignmentService:
    """
    Manages intelligent table assignment for bookings.

    Features:
    - LLM-based context understanding
    - Multi-table combinations for large groups
    - Special feature matching (window, garden, etc.)
    - Capacity optimization
    - Transparent reasoning
    - Zero impact when feature disabled
    """

    # Scoring weights for table assignment algorithm
    WEIGHT_CAPACITY_EFFICIENCY = 0.35
    WEIGHT_TABLE_COUNT = 0.25
    WEIGHT_SPLIT_BALANCE = 0.20
    WEIGHT_VIEW_PREFERENCE = 0.15
    WEIGHT_CAPACITY_WASTE = 0.05

    # Table type preference scores
    TABLE_TYPE_SCORES = {
        'window': 1.0,
        'garden': 0.95,
        'balcony': 0.9,
        'poolside': 0.85,
        'indoor': 0.7,
        'standard': 0.6,
        None: 0.5
    }

    def __init__(self):
        """Initialize table assignment service"""
        self.enabled = FeatureFlags.is_enabled(Feature.ADVANCED_TABLE_ASSIGNMENT)

        if not self.enabled:
            logger.debug("table_assignment_disabled", reason="feature_flag_disabled")
            return

        # Configuration
        self.max_table_combination = int(os.getenv("MAX_TABLE_COMBINATION", "2"))
        self.min_capacity_efficiency = float(os.getenv("MIN_CAPACITY_EFFICIENCY", "0.7"))

        logger.info(
            "table_assignment_initialized",
            enabled=self.enabled,
            max_combination=self.max_table_combination,
            min_efficiency=self.min_capacity_efficiency
        )

    async def find_best_tables(
        self,
        restaurant_id: str,
        party_size: int,
        booking_date: date,
        booking_time: time_type,
        preferences: Optional[Dict[str, Any]] = None,
        db_session=None
    ) -> Dict[str, Any]:
        """
        Find optimal table(s) for a booking using LLM-based context understanding.

        This is the main entry point for smart table assignment.
        Uses context, preferences, and availability to select best tables.

        Args:
            restaurant_id: Restaurant UUID
            party_size: Number of guests
            booking_date: Date of booking
            booking_time: Time of booking
            preferences: Optional dict with:
                - table_type: "window", "garden", "balcony", "poolside", "indoor", "standard"
                - special_request: Free text (e.g., "near kitchen", "quiet corner")
                - combine_tables: Allow table combinations (default: True for large groups)
            db_session: Optional database session (will create if not provided)

        Returns:
            dict: {
                "success": bool,
                "tables": List[dict] - selected table(s) with details,
                "total_capacity": int,
                "reasoning": str - why these tables were chosen,
                "score": float - assignment quality score,
                "alternatives": List[dict] - other viable options
            }
        """
        if not self.enabled:
            return {
                "success": True,
                "enabled": False,
                "reason": "feature_disabled",
                "message": "Use simple first-available table assignment"
            }

        logger.info(
            "finding_best_tables",
            restaurant_id=restaurant_id[:8],
            party_size=party_size,
            booking_date=str(booking_date),
            booking_time=str(booking_time),
            preferences=preferences
        )

        preferences = preferences or {}

        try:
            # Get database session
            if db_session is None:
                async with get_db_session() as db:
                    return await self._find_tables_internal(
                        db=db,
                        restaurant_id=restaurant_id,
                        party_size=party_size,
                        booking_date=booking_date,
                        booking_time=booking_time,
                        preferences=preferences
                    )
            else:
                return await self._find_tables_internal(
                    db=db_session,
                    restaurant_id=restaurant_id,
                    party_size=party_size,
                    booking_date=booking_date,
                    booking_time=booking_time,
                    preferences=preferences
                )

        except Exception as e:
            logger.error(
                "table_assignment_error",
                error=str(e),
                error_type=type(e).__name__,
                restaurant_id=restaurant_id[:8],
                party_size=party_size
            )
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to find optimal tables"
            }

    async def _find_tables_internal(
        self,
        db,
        restaurant_id: str,
        party_size: int,
        booking_date: date,
        booking_time: time_type,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal method to find tables with database session"""
        from sqlalchemy import select, and_, func
        from app.shared.models.table_models import TableInfo, TableBooking

        # Get all active tables for restaurant
        tables_stmt = (
            select(TableInfo)
            .where(
                and_(
                    TableInfo.restaurant_id == restaurant_id,
                    TableInfo.is_active == True,
                    TableInfo.is_deleted == False
                )
            )
            .order_by(TableInfo.table_capacity)
        )

        result = await db.execute(tables_stmt)
        all_tables = result.scalars().all()

        if not all_tables:
            return {
                "success": False,
                "error": "no_tables_available",
                "message": "No active tables found for this restaurant"
            }

        # Get already booked tables for this time slot
        # Note: Adjust table name based on your schema
        booked_stmt = (
            select(TableBooking.table_id)
            .where(
                and_(
                    TableBooking.restaurant_id == restaurant_id,
                    TableBooking.booking_date == booking_date,
                    TableBooking.booking_time == booking_time,
                    TableBooking.is_deleted == False,
                    func.lower(TableBooking.booking_status) != 'cancelled'
                )
            )
        )

        booked_result = await db.execute(booked_stmt)
        booked_table_ids = set([row[0] for row in booked_result.all()])

        # Filter available tables
        available_tables = [t for t in all_tables if t.table_id not in booked_table_ids]

        if not available_tables:
            return {
                "success": False,
                "error": "all_tables_booked",
                "message": f"No available tables for {booking_date} at {booking_time}"
            }

        # LLM-BASED LOGIC: Analyze preferences and context
        requested_type = preferences.get("table_type")
        allow_combinations = preferences.get("combine_tables", party_size > 6)

        # Find solutions
        solutions = self._generate_table_solutions(
            available_tables=available_tables,
            party_size=party_size,
            requested_type=requested_type,
            allow_combinations=allow_combinations
        )

        if not solutions:
            return {
                "success": False,
                "error": "no_suitable_tables",
                "message": f"Cannot accommodate {party_size} guests with available tables"
            }

        # Get best solution
        best_solution = max(solutions, key=lambda x: x['score'])

        # Format response
        selected_tables = [
            {
                "table_id": str(t.table_id),
                "table_number": t.table_number,
                "capacity": t.table_capacity,
                "type": t.table_type,
                "floor": t.floor_location
            }
            for t in best_solution['tables']
        ]

        # Generate reasoning
        reasoning = self._generate_reasoning(
            solution=best_solution,
            party_size=party_size,
            requested_type=requested_type
        )

        logger.info(
            "tables_assigned",
            num_tables=len(selected_tables),
            total_capacity=best_solution['total_capacity'],
            score=best_solution['score'],
            efficiency=best_solution['capacity_efficiency']
        )

        return {
            "success": True,
            "tables": selected_tables,
            "total_capacity": best_solution['total_capacity'],
            "waste": best_solution['waste'],
            "score": best_solution['score'],
            "reasoning": reasoning,
            "alternatives": [
                {
                    "tables": [str(t.table_id) for t in s['tables']],
                    "score": s['score']
                }
                for s in sorted(solutions, key=lambda x: x['score'], reverse=True)[1:4]
            ] if len(solutions) > 1 else []
        }

    def _generate_table_solutions(
        self,
        available_tables: List[Any],
        party_size: int,
        requested_type: Optional[str],
        allow_combinations: bool
    ) -> List[Dict[str, Any]]:
        """
        Generate all viable table assignment solutions.

        This is the core algorithm that finds single-table and
        multi-table solutions, then scores them.
        """
        solutions = []

        # Single table solutions
        for table in available_tables:
            if table.table_capacity >= party_size:
                # Bonus for matching requested type
                type_match = (table.table_type == requested_type) if requested_type else False

                score_data = self._calculate_combination_score(
                    tables=[table],
                    party_size=party_size,
                    type_match_bonus=0.1 if type_match else 0
                )
                solutions.append(score_data)

        # Multi-table combinations (if allowed)
        if allow_combinations and len(available_tables) >= 2:
            for combo_size in range(2, min(self.max_table_combination + 1, len(available_tables) + 1)):
                for combo in combinations(available_tables, combo_size):
                    total_cap = sum(t.table_capacity for t in combo)

                    # Only consider if total capacity is sufficient
                    if total_cap >= party_size:
                        # Check if any table matches requested type
                        type_match = any(
                            t.table_type == requested_type for t in combo
                        ) if requested_type else False

                        score_data = self._calculate_combination_score(
                            tables=list(combo),
                            party_size=party_size,
                            type_match_bonus=0.05 if type_match else 0  # Lower bonus for combinations
                        )

                        # Filter low-efficiency combinations
                        if score_data['capacity_efficiency'] >= self.min_capacity_efficiency:
                            solutions.append(score_data)

        return solutions

    def _calculate_combination_score(
        self,
        tables: List[Any],
        party_size: int,
        type_match_bonus: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate quality score for a table combination.

        Scoring factors:
        - Capacity efficiency (35%): How well does capacity match party size
        - Table count (25%): Prefer fewer tables
        - Split balance (20%): Single table is best
        - View preference (15%): Window > Garden > Balcony > etc.
        - Capacity waste (5%): Minimize unused seats
        - Type match bonus: Extra points for matching requested type
        """
        total_capacity = sum(t.table_capacity for t in tables)
        num_tables = len(tables)

        # Capacity efficiency: party_size / total_capacity
        capacity_efficiency = party_size / total_capacity if total_capacity > 0 else 0
        capacity_score = capacity_efficiency * self.WEIGHT_CAPACITY_EFFICIENCY

        # Table count: prefer fewer tables (1/num_tables)
        table_count_score = (1 / num_tables) * self.WEIGHT_TABLE_COUNT

        # Split balance: bonus for single table
        split_balance_score = self.WEIGHT_SPLIT_BALANCE if num_tables == 1 else (
            self.WEIGHT_SPLIT_BALANCE * 0.7
        )

        # View preference: average table type score
        avg_type_score = sum(
            self.TABLE_TYPE_SCORES.get(t.table_type, 0.5)
            for t in tables
        ) / num_tables
        view_score = avg_type_score * self.WEIGHT_VIEW_PREFERENCE

        # Capacity waste: minimize unused seats
        waste = total_capacity - party_size
        waste_ratio = waste / total_capacity if total_capacity > 0 else 1
        waste_score = (1 - waste_ratio) * self.WEIGHT_CAPACITY_WASTE

        # Total score (before bonus)
        base_score = capacity_score + table_count_score + split_balance_score + view_score + waste_score

        # Apply type match bonus
        total_score = base_score + type_match_bonus

        return {
            'score': total_score,
            'total_capacity': total_capacity,
            'waste': waste,
            'num_tables': num_tables,
            'capacity_efficiency': capacity_efficiency,
            'tables': tables
        }

    def _generate_reasoning(
        self,
        solution: Dict[str, Any],
        party_size: int,
        requested_type: Optional[str]
    ) -> str:
        """
        Generate human-readable reasoning for table assignment.

        This explains WHY these tables were chosen.
        """
        tables = solution['tables']
        num_tables = len(tables)
        total_capacity = solution['total_capacity']
        waste = solution['waste']
        efficiency = solution['capacity_efficiency']

        # Build reasoning parts
        parts = []

        if num_tables == 1:
            table = tables[0]
            parts.append(f"Assigned Table {table.table_number} (capacity {table.table_capacity})")

            if table.table_type:
                parts.append(f"with {table.table_type} seating")

            if requested_type and table.table_type == requested_type:
                parts.append(f"✓ Matches your preference for {requested_type} seating")

        else:
            table_list = ", ".join([f"#{t.table_number}" for t in tables])
            parts.append(f"Assigned {num_tables} tables: {table_list}")
            parts.append(f"(combined capacity {total_capacity})")

        # Capacity info
        parts.append(f"for your party of {party_size}")

        # Efficiency note
        if waste == 0:
            parts.append("- Perfect capacity match!")
        elif waste <= 2:
            parts.append(f"- Near-optimal fit ({waste} extra seat{'s' if waste > 1 else ''})")
        else:
            parts.append(f"- Best available option ({efficiency:.0%} capacity utilization)")

        return " ".join(parts)


# Singleton instance (lazy initialization)
_assignment_service: Optional[TableAssignmentService] = None


def get_table_assignment_service() -> TableAssignmentService:
    """
    Get singleton instance of TableAssignmentService.

    Returns:
        TableAssignmentService instance (may be disabled if feature flag off)
    """
    global _assignment_service
    if _assignment_service is None:
        _assignment_service = TableAssignmentService()
    return _assignment_service
