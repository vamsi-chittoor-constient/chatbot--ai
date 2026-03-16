"""
Menu Recommendation Tagger
==========================
LLM-based service that generates food tags for menu items.

Runs after menu preload — any item without `recommendation_tags` gets
tagged via OpenAI, and the tags are written back to PostgreSQL.

Tags are used by the recommendation engine in preloader.get_similar_items()
to find semantically related items (burger → pizza, cake → brownie, etc.)
"""

import asyncio
import json
import os
from typing import Dict, List, Optional

import structlog
from app.core.db_pool import get_async_pool

logger = structlog.get_logger(__name__)

# Batch size for LLM calls (tag multiple items per call to save tokens)
_BATCH_SIZE = 10


async def tag_untagged_items(menu_items: List[Dict]) -> List[Dict]:
    """
    Find menu items without recommendation_tags and generate them via LLM.

    Args:
        menu_items: Full menu cache (each item has id, name, description, category, price)

    Returns:
        Updated menu items with recommendation_tags populated
    """
    untagged = [item for item in menu_items if not item.get("recommendation_tags")]

    if not untagged:
        logger.debug("menu_tagger_all_tagged", total=len(menu_items))
        return menu_items

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("menu_tagger_skipped_no_api_key")
        return menu_items

    logger.info("menu_tagger_start", untagged=len(untagged), total=len(menu_items))

    # Process in batches
    all_tags: Dict[str, List[str]] = {}
    for i in range(0, len(untagged), _BATCH_SIZE):
        batch = untagged[i : i + _BATCH_SIZE]
        batch_tags = await _tag_batch(batch, api_key)
        all_tags.update(batch_tags)

    if not all_tags:
        logger.warning("menu_tagger_no_tags_generated")
        return menu_items

    # Write tags to PostgreSQL
    await _store_tags(all_tags)

    # Update in-memory cache
    tags_applied = 0
    for item in menu_items:
        if item["id"] in all_tags:
            item["recommendation_tags"] = all_tags[item["id"]]
            tags_applied += 1

    logger.info("menu_tagger_complete", tagged=tags_applied, total=len(menu_items))
    return menu_items


def _build_tagger_prompt(items: List[Dict]) -> str:
    """Build the tagging prompt for a batch of items."""
    items_text = ""
    for idx, item in enumerate(items, 1):
        items_text += (
            f"{idx}. \"{item['name']}\" | Category: {item.get('category', 'Other')} | "
            f"Price: ₹{item.get('price', 0)} | Desc: {item.get('description', 'N/A')}\n"
        )

    return f"""You are a food recommendation expert. For each menu item below, generate 5-10 recommendation tags.

Tags should capture:
- Food type (e.g. burger, pizza, rice, curry, soup, salad, sandwich, noodles)
- Cuisine (e.g. indian, chinese, continental, south_indian, north_indian, italian)
- Cooking style (e.g. grilled, fried, steamed, baked, tandoori, roasted)
- Flavor profile (e.g. spicy, sweet, savory, creamy, tangy, mild)
- Meal context (e.g. breakfast, lunch, dinner, snack, dessert, beverage, side_dish, main_course, starter)
- Dietary (e.g. vegetarian, non_vegetarian, vegan, egg)
- Ingredient highlights (e.g. chicken, paneer, fish, mushroom, cheese, chocolate)
- Food group for recommendations (e.g. comfort_food, street_food, healthy, indulgent, quick_bite)

IMPORTANT: Tags should help find SIMILAR items. Items that pair well together or substitute for each other should share tags.
For example: "Chicken Burger" and "Chicken Sandwich" should share tags like [chicken, non_vegetarian, quick_bite, grilled].

Menu items:
{items_text}

Return ONLY valid JSON — a dictionary mapping item number (as string) to array of lowercase tags.
Example: {{"1": ["chicken", "grilled", "non_vegetarian", "burger", "quick_bite", "comfort_food"], "2": ["coffee", "hot_beverage", "beverage", "caffeine"]}}"""


def _get_llm():
    """Get the LLM instance, supporting both Azure and standard OpenAI."""
    use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

    if use_azure:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI", "gpt-4.1-mini")

        if azure_endpoint and azure_key:
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_deployment=azure_deployment,
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version=azure_version,
                temperature=0,
                max_tokens=1500,
            )

    # Fallback to standard OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=1500,
            api_key=api_key,
        )

    return None


async def _tag_batch(items: List[Dict], api_key: str) -> Dict[str, List[str]]:
    """Tag a batch of items via a single LLM call."""
    prompt = _build_tagger_prompt(items)

    try:
        llm = _get_llm()
        if not llm:
            logger.warning("menu_tagger_no_llm_configured")
            return {}

        response = await asyncio.to_thread(llm.invoke, prompt)
        content = response.content.strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        parsed = json.loads(content)

        # Map numbered keys back to item IDs
        result: Dict[str, List[str]] = {}
        for idx, item in enumerate(items, 1):
            tags = parsed.get(str(idx), [])
            if isinstance(tags, list) and tags:
                # Normalize tags: lowercase, underscored
                result[item["id"]] = [
                    t.lower().strip().replace(" ", "_") for t in tags if isinstance(t, str)
                ]

        logger.info(
            "menu_tagger_batch",
            batch_size=len(items),
            tagged=len(result),
            sample=list(result.values())[:2] if result else [],
        )
        return result

    except Exception as e:
        logger.error("menu_tagger_batch_failed", error=str(e), batch_size=len(items))
        return {}


async def _store_tags(tags: Dict[str, List[str]]) -> None:
    """Write recommendation tags back to menu_item table in PostgreSQL."""
    try:
        pool = await get_async_pool()
        async with pool.acquire() as conn:
            # Batch update using executemany
            await conn.executemany(
                """
                UPDATE menu_item
                SET recommendation_tags = $1::jsonb
                WHERE menu_item_id = $2::uuid
                """,
                [(json.dumps(tag_list), item_id) for item_id, tag_list in tags.items()],
            )

        logger.info("menu_tagger_stored", count=len(tags))

    except Exception as e:
        logger.error("menu_tagger_store_failed", error=str(e))
