"""
Realms of Cyrisea - Economy System
Full economy suite:
- Dynamic pricing
- Regional supply/demand
- Faction discounts
- Crafting economy
- Trade routes
- Auction house
- Player trading
- Taxes & gold sinks
"""

import asyncio
import random
import logging

# ---------------------------------------------------------
# Dynamic pricing engine
# ---------------------------------------------------------

def calculate_price(world, item, region, faction_id=None):
    """Calculate dynamic price based on supply, demand, faction, and events."""

    base = item.value

    # Regional supply/demand
    supply = world.supply.get(region, {}).get(item.vnum, 1.0)
    demand = world.demand.get(region, {}).get(item.vnum, 1.0)

    price = base * demand / supply

    # Faction discount
    if faction_id:
        rep = world.player.factions.get(faction_id, 0)
        if rep >= 500:
            price *= 0.85
        elif rep >= 250:
            price *= 0.9

    # Event modifiers
    for eid, data in world.active_events.items():
        event = data["data"]
        if event["region"] == region:
            if event["type"] == "festival":
                price *= 0.9
            if event["type"] == "invasion":
                price *= 1.2

    return int(max(price, 1))

# ---------------------------------------------------------
# Shop system
# ---------------------------------------------------------

async def do_shop(player, args):
    """Open a shop in the current room."""

    shop = getattr(player.room, "shop", None)
    if not shop:
        await player.send("There is no shop here.")
        return

    region = getattr(player.room, "region", "unknown")

    await player.send("\033[94mShop Inventory:\033[0m")

    for vnum in shop:
        item = player.world.objects.get(vnum)
        if not item:
            continue

        price = calculate_price(player.world, item, region)
        await player.send(f"{item.short_desc} — {price} gold")

async def do_buy(player, args):
    """Buy an item from a shop."""

    shop = getattr(player.room, "shop", None)
    if not shop:
        await player.send("There is no shop here.")
        return

    item_name = args.lower()
    region = getattr(player.room, "region", "unknown")

    # Find item
    for vnum in shop:
        item = player.world.objects.get(vnum)
        if item and item_name in item.short_desc.lower():
            price = calculate_price(player.world, item, region)

            if player.gold < price:
                await player.send("You cannot afford that.")
                return

            player.gold -= price
            player.inventory.append(item.clone())

            # Increase demand slightly
            world = player.world
            world.demand.setdefault(region, {})
            world.demand[region][item.vnum] = world.demand[region].get(item.vnum, 1.0) + 0.05

            await player.send(f"You buy {item.short_desc} for {price} gold.")
            return

    await player.send("They do not sell that.")

async def do_sell(player, args):
    """Sell an item."""

    item_name = args.lower()
    region = getattr(player.room, "region", "unknown")

    for obj in list(player.inventory):
        if item_name in obj.short_desc.lower():
            price = calculate_price(player.world, obj, region) // 2

            player.inventory.remove(obj)
            player.gold += price

            # Increase supply slightly
            world = player.world
            world.supply.setdefault(region, {})
            world.supply[region][obj.vnum] = world.supply[region].get(obj.vnum, 1.0) + 0.05

            await player.send(f"You sell {obj.short_desc} for {price} gold.")
            return

    await player.send("You do not have that item.")

# ---------------------------------------------------------
# Trade routes
# ---------------------------------------------------------

async def do_trade(player, args):
    """View trade routes from this region."""

    region = getattr(player.room, "region", None)
    if not region:
        await player.send("This area has no trade routes.")
        return

    routes = player.world.trade_routes.get(region, {})
    if not routes:
        await player.send("No trade routes from here.")
        return

    await player.send("\033[95mTrade Routes:\033[0m")
    for dest, goods in routes.items():
        await player.send(f"To {dest}: {', '.join(goods)}")

# ---------------------------------------------------------
# Auction house
# ---------------------------------------------------------

async def do_auction(player, args):
    """View auction listings."""

    world = player.world
    if not world.auctions:
        await player.send("No items are currently up for auction.")
        return

    await player.send("\033[94mAuction House:\033[0m")
    for listing in world.auctions:
        item = listing["item"]
        price = listing["price"]
        seller = listing["seller"]
        await player.send(f"{item.short_desc} — {price} gold (Seller: {seller})")


async def do_bid(player, args):
    """Bid on an auction item."""

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Syntax: bid <item> <amount>")
        return

    item_name, amount_str = parts
    try:
        amount = int(amount_str)
    except ValueError:
        await player.send("Bid must be a number.")
        return

    world = player.world

    for listing in world.auctions:
        if item_name.lower() in listing["item"].short_desc.lower():
            if amount <= listing["price"]:
                await player.send("Your bid must be higher.")
                return

            listing["price"] = amount
            listing["bidder"] = player.name
            await player.send("You place a bid.")
            return

    await player.send("No such auction item.")

# ---------------------------------------------------------
# Player trading
# ---------------------------------------------------------

async def do_tradeoffer(player, args):
    """Offer an item to another player."""

    parts = args.split(maxsplit=2)
    if len(parts) < 3:
        await player.send("Syntax: tradeoffer <player> <item> <price>")
        return

    target_name, item_name, price_str = parts
    try:
        price = int(price_str)
    except ValueError:
        await player.send("Price must be a number.")
        return

    target = player.room.find_player(target_name)
    if not target:
        await player.send("They aren't here.")
        return

    # Find item
    for obj in player.inventory:
        if item_name.lower() in obj.short_desc.lower():
            target.trade_offer = {
                "item": obj,
                "price": price,
                "seller": player,
            }
            await player.send("Trade offer sent.")
            await target.send(f"{player.name} offers you {obj.short_desc} for {price} gold.")
            return

    await player.send("You do not have that item.")

async def do_accept(player, args):
    """Accept a trade offer."""

    offer = getattr(player, "trade_offer", None)
    if not offer:
        await player.send("No trade offer to accept.")
        return

    item = offer["item"]
    price = offer["price"]
    seller = offer["seller"]

    if player.gold < price:
        await player.send("You cannot afford that.")
        return

    player.gold -= price
    seller.gold += price

    seller.inventory.remove(item)
    player.inventory.append(item)

    player.trade_offer = None

    await player.send(f"You buy {item.short_desc} from {seller.name}.")
    await seller.send(f"{player.name} buys your {item.short_desc}.")

# ---------------------------------------------------------
# Taxes & gold sinks
# ---------------------------------------------------------

def apply_tax(world, amount):
    """Apply a global tax to reduce inflation."""
    tax_rate = world.tax_rate
    return int(amount * (1 - tax_rate))

COMMAND_DEFS = [
    ("shop",       do_shop,       {"position": "standing", "help_category": "economy"}),
    ("buy",        do_buy,        {"position": "standing", "help_category": "economy"}),
    ("sell",       do_sell,       {"position": "standing", "help_category": "economy"}),
    ("trade",      do_trade,      {"position": "standing", "help_category": "economy"}),
    ("auction",    do_auction,    {"position": "standing", "help_category": "economy"}),
    ("bid",        do_bid,        {"position": "standing", "help_category": "economy"}),
    ("tradeoffer", do_tradeoffer, {"position": "standing", "help_category": "economy"}),
    ("accept",     do_accept,     {"position": "standing", "help_category": "economy"}),
]
