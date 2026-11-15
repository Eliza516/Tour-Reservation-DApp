import Web3 from "web3";
import { CONTRACT_ABI, CONTRACT_ADDRESS } from "../config/contract";

export function hasMetaMask() {
  return typeof window !== "undefined" && typeof window.ethereum !== "undefined";
}

export function createWeb3Instance() {
  if (!hasMetaMask()) {
    throw new Error("Chưa phát hiện ví MetaMask. Vui lòng cài đặt MetaMask extension.");
  }
  return new Web3(window.ethereum);
}

export async function connectMetaMaskWallet() {
  const web3 = createWeb3Instance();
  const accounts = await window.ethereum.request({
    method: "eth_requestAccounts",
  });

  if (!accounts || accounts.length === 0) {
    throw new Error("Không tìm thấy tài khoản ví nào được chọn.");
  }

  const account = accounts[0];
  const balanceWei = await web3.eth.getBalance(account);
  const balanceEth = Number(web3.utils.fromWei(balanceWei, "ether")).toFixed(4);
  const chainId = Number(await web3.eth.getChainId());

  return { web3, account, balanceEth, chainId };
}

export async function getWalletSnapshot(web3, account) {
  const balanceWei = await web3.eth.getBalance(account);
  const balanceEth = Number(web3.utils.fromWei(balanceWei, "ether")).toFixed(4);
  const chainId = Number(await web3.eth.getChainId());
  return { balanceEth, chainId };
}

export function getTourContract(web3) {
  if (!CONTRACT_ADDRESS) return null;
  return new web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS);
}

export function formatShortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function getNetworkName(chainId) {
  const networks = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    31337: "Hardhat Local",
    1337: "Localhost 8545",
  };
  return networks[chainId] || `Chain ID: ${chainId}`;
}