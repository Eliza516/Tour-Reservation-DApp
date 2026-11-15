export const CONTRACT_ADDRESS = "0xAa5AfB26CFcc5Fdb6EedAeff80A6E17bD0D0902e";

export const TOUR_DEFAULT = {
  name: "Tour Du Lich Kham Pha 25 Cho",
  totalSeats: 25,
  ticketPriceEth: "0.08",
};

// ABI khop voi TourReservation.sol
export const CONTRACT_ABI = [
  {
    inputs: [],
    name: "operator",
    outputs: [{ internalType: "address", name: "", type: "address" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "ticketPrice",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "totalSeats",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "uint256", name: "_totalSeats", type: "uint256" },
      { internalType: "uint256", name: "_ticketPrice", type: "uint256" },
    ],
    name: "createTour",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [{ internalType: "uint256", name: "_seats", type: "uint256" }],
    name: "bookSeats",
    outputs: [],
    stateMutability: "payable",
    type: "function",
  },
  {
    inputs: [],
    name: "getAvailableSeats",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "getMyBookings",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
];