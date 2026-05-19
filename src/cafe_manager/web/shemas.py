from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ChairResponse(BaseModel):
    id: int | None = Field(validation_alias="chair_id")
    table_id: int | None = Field(validation_alias="_table_id")
    state: str = Field(validation_alias="_state")

    model_config = ConfigDict(from_attributes=True)


class TableResponse(BaseModel):
    id: int | None = Field(validation_alias="table_id")
    capacity: int = Field(validation_alias="max_places")
    state: str = Field(validation_alias="_state")
    chairs: list[int] = Field(validation_alias="_chairs_ids")

    model_config = ConfigDict(from_attributes=True)


class CoffeeMachineResponse(BaseModel):
    id: int | None = Field(validation_alias="machine_id")
    model: str
    state: str = Field(validation_alias="_state")
    limit: int = Field(validation_alias="maintenance_limit")
    cycles: int = Field(validation_alias="cycles_count")

    model_config = ConfigDict(from_attributes=True)


class EmployeeResponse(BaseModel):
    id: str = Field(validation_alias="employee_id")
    name: str
    state: str = Field(validation_alias="_state")
    rest_start: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientResponse(BaseModel):
    id: str = Field(validation_alias="client_id")
    name: str
    total_spent: str
    orders_amount: int
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("total_spent", mode="before")
    @classmethod
    def coerce_money(cls, v: object) -> str:
        return str(v)


class OrderResponse(BaseModel):
    id: str = Field(validation_alias="order_id")
    state: str = Field(validation_alias="_state")
    table_id: int | None
    client_id: str | None
    employee_id: str | None
    machine_id: int | None
    total_price: str = Field(validation_alias="total_price")
    created_at: datetime
    paid_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("total_price", mode="before")
    @classmethod
    def coerce_money(cls, v: object) -> str:
        return str(v)


class IngredientInfo(BaseModel):
    name: str
    amount: float
    unit: str


class MenuItemResponse(BaseModel):
    name: str
    price: str
    category: str

    @field_validator("price", mode="before")
    @classmethod
    def coerce_money(cls, v: object) -> str:
        return str(v)


class MenuInfoResponse(BaseModel):
    items: dict[str, list[MenuItemResponse]]


class InventoryResponse(BaseModel):
    name: str
    unit: str
    amount: float


class FinanceStatsResponse(BaseModel):
    id: UUID
    balance: str
    income: str
    expense: str
    profit_abs: str
    is_loss: bool

    @field_validator("balance", "income", "expense", "profit_abs", mode="before")
    @classmethod
    def coerce_money(cls, v: object) -> str:
        return str(v)


class TransactionResponse(BaseModel):
    id: UUID = Field(validation_alias="transaction_id")
    type: str = Field(validation_alias="transaction_type")
    money: str
    description: str
    time: datetime
    model_config = {"from_attributes": True}

    @field_validator("money", mode="before")
    @classmethod
    def coerce_money(cls, v: object) -> str:
        return str(v)


class CafeEnvResponse(BaseModel):
    name: str
    path: str
    is_active: bool
