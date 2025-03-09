// Abi from AgentCommunicationContract - see https://gnosisscan.io/address/0xd422e0059ed819e8d792af936da206878188e34f#code
export const abi = [
  {
    type: "function",
    name: "sendMessage",
    inputs: [
      {
        name: "agentAddress",
        type: "address",
        internalType: "address",
      },
      {
        name: "message",
        type: "bytes",
        internalType: "bytes",
      },
    ],
    outputs: [],
    stateMutability: "payable",
  },
] as const
