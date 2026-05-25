import "dotenv/config";

import OpenAI from "openai";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import {
  createPublicClient,
  formatEther,
  http,
  isAddress
} from "viem";
import { sepolia } from "viem/chains";

const rpcUrl = process.env.SEPOLIA_RPC_URL;
const model = process.env.OPENAI_MODEL || "gpt-4o-mini";

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Add it to .env first.");
  process.exit(1);
}

if (!rpcUrl) {
  console.error("Missing SEPOLIA_RPC_URL. Add it to .env first.");
  process.exit(1);
}

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL || undefined
});

const publicClient = createPublicClient({
  chain: sepolia,
  transport: http(rpcUrl)
});

async function getEthBalance(address) {
  if (!isAddress(address)) {
    throw new Error(`Invalid Ethereum address: ${address}`);
  }

  const balanceWei = await publicClient.getBalance({ address });
  const balanceEth = formatEther(balanceWei);

  return {
    address,
    chain: "Sepolia",
    balanceWei: balanceWei.toString(),
    balanceEth
  };
}

const tools = [
  {
    type: "function",
    function: {
      name: "getEthBalance",
      description: "Get the Sepolia ETH balance for a valid Ethereum address. This is read-only and never sends transactions.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          address: {
            type: "string",
            description: "Ethereum address to check, for example 0x0000000000000000000000000000000000000000."
          }
        },
        required: ["address"]
      }
    }
  }
];

async function readUserRequest() {
  const requestFromArgs = process.argv.slice(2).join(" ").trim();
  if (requestFromArgs) {
    return requestFromArgs;
  }

  const rl = readline.createInterface({ input, output });
  const answer = await rl.question("Enter your on-chain request: ");
  rl.close();
  return answer.trim();
}

async function main() {
  const userRequest = await readUserRequest();

  if (!userRequest) {
    console.error("No request provided.");
    process.exit(1);
  }

  console.log("\n[User input]");
  console.log(userRequest);

  const messages = [
    {
      role: "system",
      content: [
        "You are a beginner-friendly AI x Web3 demo agent.",
        "You can only perform read-only checks.",
        "Use getEthBalance when the user asks for a Sepolia ETH balance.",
        "Never suggest sending transactions or using private keys.",
        "Keep final answers concise."
      ].join(" ")
    },
    {
      role: "user",
      content: userRequest
    }
  ];

  const firstResponse = await openai.chat.completions.create({
    model,
    messages,
    tools,
    tool_choice: "auto"
  });

  const assistantMessage = firstResponse.choices[0]?.message;
  if (!assistantMessage) {
    throw new Error("The model did not return a message.");
  }

  messages.push(assistantMessage);

  if (!assistantMessage.tool_calls?.length) {
    console.log("\n[Model tool call]");
    console.log("No tool call requested.");

    console.log("\n[Final answer]");
    console.log(assistantMessage.content || "No answer returned.");
    return;
  }

  for (const toolCall of assistantMessage.tool_calls) {
    const functionName = toolCall.function.name;
    const functionArgs = JSON.parse(toolCall.function.arguments || "{}");

    console.log("\n[Model tool call]");
    console.log(JSON.stringify({ name: functionName, arguments: functionArgs }, null, 2));

    let toolResult;
    try {
      if (functionName !== "getEthBalance") {
        throw new Error(`Unknown tool: ${functionName}`);
      }

      toolResult = await getEthBalance(functionArgs.address);
    } catch (error) {
      toolResult = {
        error: error instanceof Error ? error.message : String(error)
      };
    }

    console.log("\n[Tool result]");
    console.log(JSON.stringify(toolResult, null, 2));

    messages.push({
      role: "tool",
      tool_call_id: toolCall.id,
      content: JSON.stringify(toolResult)
    });
  }

  const finalResponse = await openai.chat.completions.create({
    model,
    messages
  });

  const finalAnswer = finalResponse.choices[0]?.message?.content;

  console.log("\n[Final answer]");
  console.log(finalAnswer || "No final answer returned.");
}

main().catch((error) => {
  console.error("\n[Error]");
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
