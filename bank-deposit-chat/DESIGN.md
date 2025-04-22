# AI Agent for Coordinating Deposit Rates

## Functional Requirements

1. The client is provided with a chat interface where the company specifies the amount of funds to be deposited and the duration of the deposit.
2. The client is informed of the interest rate based on the bank's up-to-date deposit rate database.
3. The chat must be able to communicate with the client in free-form language, coordinating the amount and duration of the deposit.
4. Before proceeding with the deposit, the client must confirm that the AI has correctly understood the amount and duration, or be able to modify the data.

## AI Agent Graph

![graph.png](graph.png)

## Example Dialogue

```bazaar
================================ Human Message =================================

Please clarify the current balances on our accounts.
================================== Ai Message ==================================

Please specify the amount and duration for the deposit.
================================== Ai Message ==================================

[{'id': 'toolu_015Snhwrb65M4knigwQ97fGk', 'input': {}, 'name': 'get_user_free_cash', 'type': 'tool_use'}]
Tool Calls:
  get_user_free_cash (toolu_015Snhwrb65M4knigwQ97fGk)
 Call ID: toolu_015Snhwrb65M4knigwQ97fGk
  Args:
================================= Tool Message =================================
Name: get_user_free_cash

1000000
================================== Ai Message ==================================

I see that you currently have €1,000,000 in free cash available that could potentially be placed on deposit. To proceed with a deposit, I'll need you to confirm two things:
1. The specific amount you want to deposit (up to €1,000,000)
2. The duration of the deposit (between 1 and 365 days)

Once you provide those details, I can help you further with the deposit process.
================================ Human Message =================================

Yes, let's deposit the entire amount currently available in our accounts.
================================== Ai Message ==================================

Please specify the duration for the deposit amount of 1000000 euros.
================================== Ai Message ==================================



To recap, you want to deposit the entire available balance of €1,000,000, but I still need you to confirm the specific number of days you'd like to deposit the funds for (between 1 and 365 days).

Could you please tell me the exact number of days you want to place this deposit?
================================ Human Message =================================

Let's do it for 10 days.
================================== Ai Message ==================================

Understood, deposit amount of 1000000 euros for 10 days. Please confirm the correctness of the data or adjust it.
=============================== User Approval Request ===============================
Name: confirm_amount_and_duration

Please verify the correctness of the deposit amount and duration.
	 - Deposit amount: 1000000 euros
	 - Duration: 10 days
=============================== Function Message ===============================
Name: confirm_amount_and_duration

The client adjusted the data: {'deposit_amount': 505000}.
=============================== Function Message ===============================
Name: get_rates

For the given deposit conditions, current rates are 16.4-16.8% per annum. The recommended rate is 16.4%.
================================== Ai Message ==================================

Dear Client,

I'm writing to confirm the details of your deposit:
- Amount: 505,000 euros
- Term: 10 days
- Interest Rate: 16.4%

The deposit has been processed according to these specifications.
```
