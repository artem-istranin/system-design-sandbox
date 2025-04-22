import time
from typing import Annotated
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, FunctionMessage, AIMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from deposit_rates_db import get_deposit_rates_range, init_db_with_dummy_data
from utils import validate_required_env_vars

load_dotenv()

llm = ChatAnthropic(model='claude-3-5-haiku-latest')


# ---------------- Graph state ----------------
class State(TypedDict):
    messages: Annotated[list, add_messages]
    deposit_amount: int
    deposit_duration: int
    min_rate: float
    max_rate: float
    agreed_rate: float


# --------------- Nodes ----------------
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


class DepositConditions(BaseModel):
    deposit_amount: int = Field(
        description="Amount of money user would like to allocate for a deposit in RUB. "
                    "Set amount value to -1 if user didn't tell it yet."
    )
    deposit_duration: int = Field(
        description="Duration of deposit in days - latest duration provided by user."
                    "Set amount value to -1 if user didn't tell it yet."
    )


def extract_amount_and_duration(state: State):
    """Extract deposit amount and duration from user message."""
    deposit_conditions_llm = llm.with_structured_output(DepositConditions)
    deposit_cond_check = deposit_conditions_llm.invoke(state["messages"])

    extraction_res = {}
    is_deposit_amount_provided = False
    if deposit_cond_check.deposit_amount > 0:
        extraction_res["deposit_amount"] = deposit_cond_check.deposit_amount
        is_deposit_amount_provided = True
    is_deposit_duration_provided = False
    if deposit_cond_check.deposit_duration > 0:
        extraction_res["deposit_duration"] = deposit_cond_check.deposit_duration
        is_deposit_duration_provided = True

    if is_deposit_amount_provided and is_deposit_duration_provided:
        msg = (f'Понятно, размещение {deposit_cond_check.deposit_amount} рублей сроком '
               f'на {deposit_cond_check.deposit_duration} дней. '
               f'Пожалуйста, подтвердите корректрость данных или скорректируйте.')
    elif is_deposit_amount_provided and not is_deposit_duration_provided:
        msg = (f'Уточните, пожалуйста, на какой срок хотели бы разместить {deposit_cond_check.deposit_amount} рублей.')
    elif not is_deposit_amount_provided and is_deposit_duration_provided:
        msg = (f'Уточните, пожалуйста, какую сумму хотели бы разместить на {deposit_cond_check.deposit_duration} дней.')
    else:
        msg = (f'Уточните, пожалуйста, сумму и срок для размещения депозита.')
    extraction_res["messages"] = [AIMessage(msg)]

    return Command(update=extraction_res)


def is_amount_and_duration_provided(state: State):
    if 'deposit_amount' in state and 'deposit_duration' in state:
        return 'Amount and duration are provided'
    return 'Not enough info'


def confirm_amount_and_duration(state: State):
    deposit_amount = state["deposit_amount"]
    deposit_duration = state["deposit_duration"]

    human_response = interrupt(
        {
            "question": "Пожалуйста, проверьте корректрость суммы и срока депозита.",
            "deposit_amount": deposit_amount,
            "deposit_duration": deposit_duration,
            "name": "confirm_amount_and_duration",
        },
    )
    if human_response.get("correct", "").lower().startswith("y"):
        verified_deposit_amount = deposit_amount
        verified_deposit_duration = deposit_duration
        response = "Клиент подтвердил корректность данных."
    else:
        verified_deposit_amount = human_response.get("deposit_amount", deposit_amount)
        verified_deposit_duration = human_response.get("deposit_duration", deposit_duration)
        response = f"Клиент скорректировал данные: {human_response}."

    msg = FunctionMessage(response, name="confirm_amount_and_duration")

    state_update = {
        "deposit_amount": verified_deposit_amount,
        "deposit_duration": verified_deposit_duration,
        "messages": [msg],
    }
    return state_update


def get_rates(state: State):
    """Get deposit rates for requested amount and duration."""
    min_r, max_r = get_deposit_rates_range(state['deposit_amount'], state['deposit_duration'])
    msg = FunctionMessage(content=f"Для данных условий размещения текущие ставки {min_r}-{max_r}% годовых. "
                                  f"Рекоммендованная ставка {min_r}%.", name="get_rates")
    return {"min_rate": min_r, "max_rate": max_r, "agreed_rate": min_r, "messages": [msg]}


def finalize_offer(state: State):
    """Make a deposit summary."""
    llm_response = llm.invoke(f"Проинформируй клиента о рамещении в коротком сообщении: "
                              f"{state['deposit_amount']} рублей на {state['deposit_duration']} дней "
                              f"по ставке {state['agreed_rate']}%. "
                              f"Без дополнительных вопросов к клинету, только информирование.")
    return {"messages": [AIMessage(llm_response.content)]}


# --------------- Tools ----------------
@tool
def get_user_free_cache() -> int:
    """Получить объем свободных денежных средств на счетах у клиента, которые потенциально
    могут быть размещены на депозит."""
    return 1000000


if __name__ == '__main__':
    validate_required_env_vars()
    init_db_with_dummy_data()

    tools = [get_user_free_cache]
    llm_with_tools = llm.bind_tools(tools)

    # --------------- Build workflow ----------------
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("extract_amount_and_duration", extract_amount_and_duration)
    graph_builder.add_node("confirm_amount_and_duration", confirm_amount_and_duration)
    graph_builder.add_node("get_rates", get_rates)
    graph_builder.add_node("finalize_offer", finalize_offer)
    graph_builder.add_node("tools", ToolNode(tools=tools))

    # Add edges to connect nodes
    graph_builder.add_edge(START, "extract_amount_and_duration")
    graph_builder.add_conditional_edges(
        "extract_amount_and_duration",
        is_amount_and_duration_provided,
        {
            'Amount and duration are provided': "confirm_amount_and_duration",
            'Not enough info': "chatbot"
        }
    )
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge("confirm_amount_and_duration", "get_rates")
    graph_builder.add_edge("get_rates", "finalize_offer")
    graph_builder.add_edge("finalize_offer", END)

    # Compile
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    # --------------- Visualize workflow ----------------
    # png_bytes = graph.get_graph().draw_mermaid_png()
    # with open("graph.png", "wb") as f:
    #     f.write(png_bytes)

    # --------------- Start test conversation ----------------
    config = {"configurable": {"thread_id": time.strftime('%Y%m%d_%H%M%S')}}

    # mocked_user_messages = [
    #     HumanMessage("Добрый день!"),
    #     HumanMessage("Хотели бы разместить депозит у вас в банке. Какие сейчас ставки?"),
    #     HumanMessage("На 5 дней рассматриваем размещение. Что можете преджодить?"),
    #     HumanMessage("Давайте разместим всю сумму наших текущих остатов на счетах. Можем даже на 10 дней!"),
    # ]
    mocked_user_messages = [
        HumanMessage("Уточните, пожалуйста, текущие остатки на наших счетах."),
        HumanMessage("Да, давайте разместим всю сумму наших текущих остатов на счетах."),
        HumanMessage("Давайте сделаем на 10 дней."),
    ]
    system_msg = SystemMessage("Ты ассистент ответственный за продоставление ставок размещения "
                               "денежных средств компании на депозит нашего банка Сбер. "
                               "Твоя задача получить от клиента сумму депозита и срок, на который клиент хочет разместить "
                               "депозит. Любая сумма до 100000000 и любой срок от 1 дня до 365 дней. "
                               "Разговаривай только на русском языке. Твоя цель только получить данные. "
                               "Избегай предоставления консультаций или ставок клиенту - "
                               "ставки известны только после того как сумма и период депозита известны.")

    for i, user_msg in enumerate(mocked_user_messages):

        next_messages = []
        if i == 0:
            next_messages.append(system_msg)
        next_messages.append(user_msg)

        events = graph.stream(
            {"messages": next_messages},
            config=config,
            stream_mode="values",
        )
        for event in events:
            if "messages" in event:
                event["messages"][-1].pretty_print()

    interr = graph.get_state(config)[-1][0].interrupts[0].value
    print(f'=============================== User Approval Request ===============================')
    print(f'Name: {interr["name"]}', end='\n\n')
    print(interr['question'])
    print(f"\t - Размещение {interr['deposit_amount']} рублей")
    print(f"\t - Сроком на {interr['deposit_duration']} дней")

    human_command = Command(resume={"deposit_amount": 505000})
    events = graph.stream(human_command, config=config, stream_mode="values")
    for i, event in enumerate(events):
        if i == 0:
            continue  # skip first message after interruption to not repeat the last message before interruption
        if "messages" in event:
            event["messages"][-1].pretty_print()
