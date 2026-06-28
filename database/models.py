from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Float, DateTime,
    Boolean, ForeignKey, Text, Index,
)
from sqlalchemy.orm import relationship
from database.base import Base


def utcnow():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), default="")
    level = Column(Integer, default=1)
    xp = Column(BigInteger, default=0)
    coins = Column(BigInteger, default=100)
    epic_coins = Column(BigInteger, default=0)
    current_quest = Column(String(100), default="")
    quest_target = Column(Integer, default=0)
    quest_progress = Column(Integer, default=0)
    quest_reward = Column(BigInteger, default=0)
    quest_assigned_at = Column(DateTime, default=utcnow)
    quest_completed = Column(Boolean, default=False)       # True when objective met
    quest_type = Column(String(50), default="")            # hunt, adventure, craft, gambling, arena, miniboss, cooking, guild, trading
    quest_mob = Column(String(50), default="")             # mob name for hunt/adventure
    quest_material = Column(String(50), default="")        # material name for craft
    quest_item_reward = Column(String(50), default="")     # specific item reward
    quest_item_reward_amount = Column(Integer, default=0)  # reward item count
    quest_coins_reward = Column(BigInteger, default=0)     # coins reward
    quest_xp_reward = Column(BigInteger, default=0)        # xp reward
    quest_cooldown_until = Column(DateTime, default=utcnow)  # 1h cooldown after decline
    epic_quest_wave = Column(Integer, default=0)
    epic_quest_last = Column(DateTime, default=utcnow)
    bank = Column(BigInteger, default=0)
    coolness = Column(Integer, default=0)
    area = Column(Integer, default=1)
    max_area = Column(Integer, default=1)
    tt_count = Column(Integer, default=0)
    current_hp = Column(Integer, default=0)  # 0 = needs init on first fight/heal
    life_boost_active = Column(Boolean, default=False)  # life boost potion active
    title = Column(String(100), default="")
    lang = Column(String(2), default="ru")  # "en" or "ru"
    ascended = Column(Boolean, default=False)
    inventory_data = Column(Text, default='{}')
    last_active = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)
    # Cook stat boosts (permanent until TT)
    cook_hp_boost = Column(Integer, default=0)
    cook_atk_boost = Column(Integer, default=0)
    cook_def_boost = Column(Integer, default=0)
    cook_level_boost = Column(Integer, default=0)
    # Cook multipliers (permanent until TT)
    cook_coins_mult = Column(Integer, default=0)
    cook_fish_mult = Column(Integer, default=0)
    cook_logs_mult = Column(Integer, default=0)
    cook_flat_coins = Column(Integer, default=0)

    inventory = relationship("Inventory", uselist=False, back_populates="user", cascade="all, delete-orphan")
    cooldowns = relationship("Cooldown", uselist=False, back_populates="user", cascade="all, delete-orphan")
    pets = relationship("Pet", back_populates="user", cascade="all, delete-orphan")
    guild_member = relationship("GuildMember", uselist=False, back_populates="user", cascade="all, delete-orphan")
    horse = relationship("Horse", uselist=False, back_populates="user", cascade="all, delete-orphan")
    profession = relationship("Profession", uselist=False, back_populates="user", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventories"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    materials = Column(Text, default='{"wooden_log": 0, "epic_log": 0, "super_log": 0, "mega_log": 0, "hyper_log": 0, "ultra_log": 0, "ultimate_log": 0, "normie_fish": 0, "golden_fish": 0, "epic_fish": 0, "super_fish": 0, "mega_fish": 0, "hyper_fish": 0, "apple": 0, "banana": 0, "potato": 0, "carrot": 0, "bread": 0, "Watermelon": 0, "wolfskin": 0, "zombieeye": 0, "unicornhorn": 0, "mermaid_hair": 0, "ruby": 0, "chip": 0, "coin": 0, "dragonscale": 0, "lotteryticket": 0, "life_potion": 0, "arenacookie": 0, "common_lootbox": 0, "uncommon_lootbox": 0, "rare_lootbox": 0, "epic_lootbox": 0, "edgy_lootbox": 0, "omega_lootbox": 0, "godly_lootbox": 0, "heart": 0, "dragonessence": 0, "timedragonessence": 0, "epic_berries": 0, "horse_coins": 0, "seed": 0, "smol_coin": 0, "magic_bed": 0, "omega_horse_token": 0}')
    equipment = Column(Text, default='{"weapon_tier": 1, "armor_tier": 1}')
    tools = Column(Text, default='{"axe": 1, "pickaxe": 1, "rod": 1}')
    artifacts = Column(Text, default='[]')

    user = relationship("User", back_populates="inventory")


class Cooldown(Base):
    __tablename__ = "cooldowns"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    hunt_last = Column(DateTime, default=datetime.min)
    adventure_last = Column(DateTime, default=datetime.min)
    chop_last = Column(DateTime, default=datetime.min)
    mine_last = Column(DateTime, default=datetime.min)
    fish_last = Column(DateTime, default=datetime.min)
    guild_raid_last = Column(DateTime, default=datetime.min)
    last_daily = Column(DateTime, default=datetime.min)
    last_weekly = Column(DateTime, default=datetime.min)
    last_vote = Column(DateTime, default=datetime.min)
    last_arena = Column(DateTime, default=datetime.min)
    last_duel = Column(DateTime, default=datetime.min)
    last_training = Column(DateTime, default=datetime.min)
    last_farm = Column(DateTime, default=datetime.min)
    daily_streak = Column(Integer, default=0)  # consecutive daily claims
    vote_streak = Column(Integer, default=0)  # consecutive vote streak (0-7)

    user = relationship("User", back_populates="cooldowns")


class Pet(Base):
    __tablename__ = "pets"

    pet_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    pet_type = Column(String(20), nullable=False)       # turtle, dragon, dog, cat...
    pet_tier = Column(String(5), default="I")            # I, II, III, ... XXV
    pet_score = Column(Integer, default=1)
    skill = Column(String(20), default="normie")         # normie, fast, clever, etc.
    skill_rank = Column(String(3), default="F")          # F, E, D, C, B, A, S, SS, SS+
    pet_level = Column(Integer, default=1)
    status = Column(String(20), default="idle")          # idle, adventure, tournament
    adventure_type = Column(String(10), nullable=True)   # find, learn, drill
    adventure_started_at = Column(DateTime, nullable=True)
    adventure_ready_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="pets")

    __table_args__ = (Index("idx_pets_user", "user_id"),)


class Guild(Base):
    __tablename__ = "guilds"

    guild_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    owner_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(BigInteger, default=0)
    materials = Column(Text, default='{}')
    created_at = Column(DateTime, default=utcnow)

    members = relationship("GuildMember", back_populates="guild", cascade="all, delete-orphan")


class GuildMember(Base):
    __tablename__ = "guild_members"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    guild_id = Column(Integer, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False)
    rank = Column(String(20), default="member")

    user = relationship("User", back_populates="guild_member")
    guild = relationship("Guild", back_populates="members")


class Horse(Base):
    __tablename__ = "horses"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    name = Column(String(50), default="Starter Horse")
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    tier = Column(Integer, default=1)           # 1-10
    horse_type = Column(String(20), default="normal")  # normal, defender, strong, tank, golden, magic, festive, special, super_special
    epicness = Column(Integer, default=0)       # 0-99
    fail_count = Column(Integer, default=0)     # breeding fails (guaranteed tier up after N)
    coins = Column(BigInteger, default=0)       # coins stored in horse
    last_breed_race = Column(DateTime, default=utcnow)  # shared 24h cooldown for breed+race

    user = relationship("User", back_populates="horse")


class Profession(Base):
    __tablename__ = "professions"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    worker_level = Column(Integer, default=1)
    worker_xp = Column(BigInteger, default=0)
    crafter_level = Column(Integer, default=1)
    crafter_xp = Column(BigInteger, default=0)
    lootboxer_level = Column(Integer, default=1)
    lootboxer_xp = Column(BigInteger, default=0)
    merchant_level = Column(Integer, default=1)
    merchant_xp = Column(BigInteger, default=0)
    enchanter_level = Column(Integer, default=1)
    enchanter_xp = Column(BigInteger, default=0)
    claimed = Column(Text, default='{}')

    user = relationship("User", back_populates="profession")


class Lottery(Base):
    __tablename__ = "lottery"

    lottery_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    numbers = Column(String(20), nullable=False)
    drawn = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)


class Marriage(Base):
    __tablename__ = "marriages"

    marriage_id = Column(Integer, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    user2_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    married_at = Column(DateTime, default=utcnow)


class ReturningEvent(Base):
    __tablename__ = "returning_events"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    started_at = Column(DateTime, default=utcnow)
    superdaily_day = Column(Integer, default=0)          # 0-6, next day to claim
    quest_collected_smol = Column(Integer, default=0)    # smol coins collected
    quest_shop_buys = Column(Integer, default=0)         # items bought from returning shop
    quest_superdaily_claims = Column(Integer, default=0) # super dailies claimed
    shop_purchases = Column(Text, default='{}')          # {"edgy_lootbox": 5, ...}
    quest_claimed = Column(Boolean, default=False)
