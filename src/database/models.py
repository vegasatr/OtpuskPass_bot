import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship # Импортируем relationship

Base = declarative_base()


class UserRole(enum.Enum):
    USER = "user"
    OWNER = "owner"
    ADMIN = "admin"


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# ПЕРЕМЕЩЕНО: Класс ReferralBonus теперь определяется до класса User,
# чтобы избежать NameError при ссылке на ReferralBonus.user_id в User.
class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bonus_month_given_date = Column(DateTime, nullable=False)

    # Отношение к пользователю, который заработал этот бонус
    # Это заработано THIS пользователем (user_id)
    earning_user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="earned_bonuses"
    )

    # Отношение к пользователю, который был приглашен
    invited_user = relationship(
        "User",
        foreign_keys=[invited_user_id]
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    status = Column(String, default="active")
    current_nights = Column(Integer, default=0)
    referral_code = Column(String, unique=True)
    # referrer_id указывает на пользователя, который пригласил ТЕКУЩЕГО пользователя
    referrer_id = Column(Integer, ForeignKey("users.id"))
    registration_date = Column(DateTime, default=datetime.utcnow)
    role = Column(Enum(UserRole), default=UserRole.USER)

    # Отношения
    subscriptions = relationship("Subscription", back_populates="user")
    bookings = relationship("Booking", back_populates="user")

    # Отношение для бонусов, заработанных ЭТИМ пользователем
    earned_bonuses = relationship(
        "ReferralBonus",
        foreign_keys="[ReferralBonus.user_id]",
        back_populates="earning_user",
        primaryjoin="User.id == ReferralBonus.user_id"
    )

    # Отношение для того, кто пригласил ЭТОГО пользователя (Many-to-One)
    referrer = relationship(
        "User",
        foreign_keys=[referrer_id],
        remote_side=[id],
        back_populates="invited_users"
    )

    # Отношение для пользователей, которых ЭТОТ пользователь пригласил (One-to-Many)
    invited_users = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrer"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    accumulated_nights = Column(Integer, default=0)
    payment_token = Column(String)
    amount_rub = Column(Float, nullable=False)
    amount_ton = Column(Float, nullable=False)

    # Отношения
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    description = Column(String)
    video_url = Column(String)
    features = Column(String)
    nearby_attractions = Column(String)
    status = Column(String, default="available")
    area_sqm = Column(Float)
    num_bedrooms = Column(Integer, default=1)
    apartment_type = Column(String, default="Base")
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Отношения
    bookings = relationship("Booking", back_populates="apartment")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    nights_used = Column(Integer, nullable=False)
    status = Column(String, default="pending")

    # Отношения
    user = relationship("User", back_populates="bookings")
    apartment = relationship("Apartment", back_populates="bookings")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount_ton = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    ton_address = Column(String, nullable=False)

    subscription = relationship("Subscription", back_populates="payments")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_rub = Column(Float, nullable=False)
    amount_ton = Column(Float, nullable=False)
    transaction_hash = Column(String, unique=True)
    status = Column(String, default="pending")
    type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)