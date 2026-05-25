# AI x Web3 Read-Only Agent Demo

This is a minimal Node.js CLI demo showing an AI agent flow that can read a Sepolia ETH balance.

The app:

1. Accepts a natural language request.
2. Sends the request to an OpenAI-compatible LLM with tool calling enabled.
3. Lets the model decide whether to call `getEthBalance`.
4. Uses `viem` to read the Sepolia ETH balance through an RPC URL.
5. Sends the tool result back to the model.
6. Prints a concise human-readable final answer.

This demo is read-only. It does not use private keys and cannot send transactions.

## Setup

Install dependencies:

```bash
cd demo/onchain-agent
npm install
```

Create your local environment file:

```bash
cp .env.example .env
```

Fill in `.env`:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
```

`OPENAI_BASE_URL` is optional. Leave it empty for OpenAI, or set it if you use an OpenAI-compatible provider.

## Usage

Run the interactive CLI:

```bash
npm start
```

Example prompt:

```text
Check the Sepolia ETH balance of 0x0000000000000000000000000000000000000000
```

Run the built-in demo command:

```bash
npm run demo
```

## Console Logs

The CLI prints each step clearly:

- user input
- model tool call
- tool result
- final answer

## Safety Notes

- No private keys are used.
- No wallet signing is included.
- No transactions are sent.
- The only local tool is `getEthBalance(address)`, which performs a read-only Sepolia RPC call.
